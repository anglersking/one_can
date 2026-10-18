#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CANable 2.0 / slcan 固件的最小发送/监听脚本。

依赖:
    pip install pyserial

Windows:
    python slcan_test.py --port COM4 --bitrate 500000 --id 0x7FE --data 1122334455667788

Linux:
    python3 slcan_test.py --port /dev/ttyACM0 --bitrate 500000 --id 0x7FE --data 1122334455667788

只监听（静默模式，不发帧、不应答）:
    python slcan_test.py --port COM4 --bitrate 500000 --listen 3

周期发送（每 200 ms 一帧，共 50 帧）:
    python slcan_test.py --port COM4 --bitrate 500000 --id 0x7FE --data 1122334455667788 --period 0.2 --count 50

周期发送直到 Ctrl+C:
    python slcan_test.py --port COM4 --bitrate 500000 --id 0x7FE --data 1122334455667788 --period 0.2

发送 CAN FD（需要 FD 收发器，数据段默认 2M）:
    python slcan_test.py --port COM4 --bitrate 500000 --fd --id 0x123 --data 112233445566778899AABB
    python slcan_test.py --port COM4 --bitrate 500000 --fd --no-brs --id 0x123 --data 11223344

注意:
- slcan 固件对配置命令不返回 ACK/NACK，只有 V/E 和收到的帧会回数据。
- E=0 只代表固件层没有发送失败，不代表总线上有节点 ACK。
- 发送前请确认 CAN_H/CAN_L/GND 已接好，波特率和总线一致。
"""

import argparse
import sys
import time

try:
    import serial
except ImportError:
    print("缺少 pyserial，请先执行: pip install pyserial", file=sys.stderr)
    raise SystemExit(1)

# 法例式 slcan 的 S 命令
BITRATE_CMD = {
    10000: "S0",
    20000: "S1",
    50000: "S2",
    100000: "S3",
    125000: "S4",
    250000: "S5",
    500000: "S6",
    750000: "S7",
    1000000: "S8",
    83300: "S9",
}

# CAN FD 长度 -> DLC 字符
FD_DLC = {
    0: "0", 1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
    12: "9", 16: "A", 20: "B", 24: "C", 32: "D", 48: "E", 64: "F",
}


def read_available(ser, wait=0.2, size=8192):
    time.sleep(wait)
    return ser.read(size)


def cmd(ser, text, wait=0.2):
    ser.write(text.encode("ascii") + b"\r")
    ser.flush()
    return read_available(ser, wait)


def show(label, data):
    if not data:
        print("%-10s (无数据)" % label)
        return
    try:
        print("%-10s %s" % (label, repr(data.decode("ascii", "replace"))))
    except Exception:
        print("%-10s %s" % (label, data.hex()))


def parse_data(text):
    text = text.replace(" ", "").replace(":", "").replace("-", "")
    if len(text) % 2:
        raise ValueError("数据必须是偶数个十六进制字符")
    return bytes.fromhex(text)


def build_frame(can_id, data, extended, fd, brs):
    if fd:
        if len(data) not in FD_DLC:
            raise ValueError("CAN FD 长度必须是 0-8/12/16/20/24/32/48/64，当前 %d" % len(data))
        prefix = "b" if brs else "d"
        if extended:
            prefix = prefix.upper()
        id_text = ("%08X" if extended else "%03X") % can_id
        return "%s%s%s%s" % (prefix, id_text, FD_DLC[len(data)], data.hex().upper())

    if len(data) > 8:
        raise ValueError("经典 CAN 最多 8 字节；要发 FD 请加 --fd")
    prefix = "T" if extended else "t"
    id_text = ("%08X" if extended else "%03X") % can_id
    return "%s%s%d%s" % (prefix, id_text, len(data), data.hex().upper())


def main():
    ap = argparse.ArgumentParser(description="CANable 2.0 slcan 发送/监听测试")
    ap.add_argument("--port", required=True, help="Windows: COM4；Linux: /dev/ttyACM0")
    ap.add_argument("--bitrate", type=int, default=500000, help="仲裁段波特率，默认 500000")
    ap.add_argument("--id", default="0x7FE", help="CAN ID，默认 0x7FE")
    ap.add_argument("--data", default="1122334455667788", help="十六进制数据，默认 1122334455667788")
    ap.add_argument("--extended", action="store_true", help="使用 29 位扩展 ID")
    ap.add_argument("--fd", action="store_true", help="发送 CAN FD 帧")
    ap.add_argument("--no-brs", action="store_true", help="FD 帧不带 BRS")
    ap.add_argument("--data-bitrate", type=int, choices=[2000000, 5000000], default=2000000,
                    help="FD 数据段波特率，默认 2000000（Y2），可选 5000000（Y5）")
    ap.add_argument("--listen", type=float, default=0, help="静默监听秒数（只收不发）")
    ap.add_argument("--no-send", action="store_true", help="打开通道但不发帧")
    ap.add_argument("--period", type=float, default=0.0, help="周期发送间隔（秒），0=只发一次")
    ap.add_argument("--count", type=int, default=0, help="周期发送次数，0=一直发到 Ctrl+C")
    ap.add_argument("--quiet", action="store_true", help="周期发送时不逐帧打印")
    ap.add_argument("--baud", type=int, default=115200, help="USB CDC 波特率，固件忽略，默认 115200")
    args = ap.parse_args()

    can_id = int(args.id, 0)
    max_id = 0x1FFFFFFF if args.extended else 0x7FF
    if not 0 <= can_id <= max_id:
        print("ID 超出范围（标准帧 0x000-0x7FF，扩展帧 0x0-0x1FFFFFFF）", file=sys.stderr)
        return 2
    if args.bitrate not in BITRATE_CMD:
        print("不支持的波特率，可选: %s" % ", ".join(str(x) for x in sorted(BITRATE_CMD)), file=sys.stderr)
        return 2

    data = parse_data(args.data)
    frame = build_frame(can_id, data, args.extended, args.fd, not args.no_brs)

    print("port=%s bitrate=%d id=0x%X extended=%s fd=%s" %
          (args.port, args.bitrate, can_id, args.extended, args.fd))
    print("frame=%s" % frame)

    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.2, write_timeout=1)
    except Exception as e:
        print("打开串口失败: %s" % e, file=sys.stderr)
        return 1

    try:
        time.sleep(0.2)
        ser.reset_input_buffer()
        show("V", cmd(ser, "V"))
        show("E", cmd(ser, "E"))

        if args.listen > 0:
            print("--- 静默监听 %.1f 秒 ---" % args.listen)
            cmd(ser, "C")
            cmd(ser, BITRATE_CMD[args.bitrate])
            if args.fd:
                cmd(ser, "Y2" if args.data_bitrate == 2000000 else "Y5")
            cmd(ser, "M1")           # bus monitoring，只收不发
            cmd(ser, "O")
            end = time.time() + args.listen
            buf = b""
            while time.time() < end:
                chunk = ser.read(4096)
                if chunk:
                    buf += chunk
            show("RX", buf)
            cmd(ser, "C")
            return 0

        # 正常模式：关闭自动重传，只尝试发一次，避免无 ACK 时反复重发
        cmd(ser, "C")
        cmd(ser, "M0")
        cmd(ser, "A0")
        cmd(ser, BITRATE_CMD[args.bitrate])
        if args.fd:
            cmd(ser, "Y2" if args.data_bitrate == 2000000 else "Y5")
        cmd(ser, "O")

        if not args.no_send:
            period = max(0.0, args.period)
            count = max(0, args.count)
            if period == 0 and count == 0:
                count = 1  # 默认单次发送

            if period > 0:
                print("周期发送：间隔 %.3f s，次数 %s（Ctrl+C 停止）" %
                      (period, "无限" if count == 0 else count))
            sent = 0
            try:
                while True:
                    ser.write(frame.encode("ascii") + b"\r")
                    ser.flush()
                    sent += 1
                    if not args.quiet:
                        print("%s TX #%-6d %s" % (time.strftime("%H:%M:%S"), sent, frame))

                    # 顺手收一下总线报文，避免串口缓冲堆积
                    rx = ser.read(4096)
                    if rx:
                        show("RX", rx)

                    if count and sent >= count:
                        break
                    if period > 0:
                        time.sleep(period)
            except KeyboardInterrupt:
                print("\n用户中断，已发送 %d 帧" % sent)
            except serial.SerialException as e:
                print("\n串口异常: %s" % e, file=sys.stderr)

            time.sleep(0.2)
            show("after TX", ser.read(8192))
            show("E", cmd(ser, "E"))
        else:
            print("已打开通道，--no-send 未发送")

        cmd(ser, "C")
        return 0
    finally:
        ser.close()


if __name__ == "__main__":
    raise SystemExit(main())
