# 示例代码

## 文件

| 文件 | 说明 |
|---|---|
| `slcan_test.py` | **实测可用的 slcan 原生串口脚本**，支持发送经典 CAN / CAN FD、静默监听 |
| `../BYZT-CANable2.0资料/09-Python-can使用/can_test.py` | 原始 python-can 示例（slcan） |
| `../BYZT-CANable2.0资料/09-Python-can使用/python-can.py` | 原始 python-can 示例（socketcan / slcan / pcan 注释） |

`slcan_test.py` 不依赖 python-can，只依赖 `pyserial`，因为它直接发 slcan 文本命令，能顺便测试 CAN FD 扩展命令。

## 安装

```bash
pip install pyserial
# 或者 Windows: py -m pip install pyserial
```

## Windows

先确认设备管理器里的 COM 口（例如 `COM4`）：

```powershell
python examples\slcan_test.py --port COM4 --bitrate 500000 --id 0x7FE --data 1122334455667788
```

只监听，不发帧（静默模式，不会 ACK 总线）：

```powershell
python examples\slcan_test.py --port COM4 --bitrate 500000 --listen 3
```

正常模式监听（会 ACK 对方，但不发帧，适合和第二个节点互测）：

```powershell
python examples\slcan_test.py --port COM4 --bitrate 500000 --listen-normal 15
```

周期发送（每 200 ms 一帧，共 50 帧）：

```powershell
python examples\slcan_test.py --port COM4 --bitrate 500000 --id 0x7FE --data 1122334455667788 --period 0.2 --count 50
```

一直发到按 `Ctrl+C`：

```powershell
python examples\slcan_test.py --port COM4 --bitrate 500000 --id 0x7FE --data 1122334455667788 --period 0.2
```

> 周期发送默认会先发 `A0` 关闭自动重传，每帧只尝试一次。
> 如果总线上没有节点 ACK，TX FIFO 会逐渐占满，`E` 可能变成非 0；这是正常的，接上总线或减小发送频率即可。
> 高频发送时可以加 `--quiet` 不逐帧打印。

## Linux

先确认串口：

```bash
ls /dev/ttyACM*
```

然后：

```bash
python3 examples/slcan_test.py --port /dev/ttyACM0 --bitrate 500000 --id 0x7FE --data 1122334455667788
```

也可以不用这个脚本，直接用 can-utils：

```bash
sudo slcand -o -c -s6 /dev/ttyACM0 can0
sudo ip link set can0 up
cansend can0 7FE#1122334455667788
candump can0
```

## CAN FD

需要板上收发器是 `TJA1051T-3` 或同级 FD 收发器，candleLight 固件不行。

```powershell
# FD + BRS，标准 ID，12 字节（DLC=9），数据段 2M
python examples\slcan_test.py --port COM4 --bitrate 500000 --fd --id 0x123 --data 112233445566778899AABBCC

# FD 不带 BRS
python examples\slcan_test.py --port COM4 --bitrate 500000 --fd --no-brs --id 0x123 --data 11223344
```

脚本会自动把长度映射成 DLC：`0-8` 原样，`12→9`、`16→A`、`20→B`、`24→C`、`32→D`、`48→E`、`64→F`。
数据段默认 2M（`Y2`）；要 5M 加 `--data-bitrate 5000000`（`Y5`）。

## 和 T-2Can（MCP2515）互测

T-2Can 的 MCP2515 在 **CAN A** 上，接线用 P2 端子：

| CANable | T-2Can P2（CAN A） |
|---|---|
| `CAN_H` | `CANHA` |
| `CAN_L` | `CANLA` |
| `GND` | `SGNDA`（隔离侧地） |

- 两边都设 **500 kbit/s**。
- 断电测 `CAN_H`-`CAN_L`，约 **60Ω** 说明两端各有一个 120Ω；如果只有 120Ω，把 CANable 的 P2 终端跳线接上。
- T-2Can 用 USB-C 或 24V 供电，CAN 侧是隔离的；把 CANable 的 GND 接到 `SGNDA`，不要接到 24V。

出厂固件上电后会先连 WiFi，最多等约 40 秒才初始化 CAN，所以上电后等一会儿。它每 3 秒轮流发：

- CAN A：ID `0xAA`，8 字节 `08 07 06 05 04 03 02 01`
- CAN B：ID `0xBB`，8 字节 `01 02 03 04 05 06 07 08`

### 方向 1：T-2Can → CANable

```powershell
python examples\slcan_test.py --port COM4 --bitrate 500000 --listen-normal 15
```

用 `--listen-normal`（不是 `--listen`），因为正常模式会 ACK 对方；静默模式不 ACK，T-2Can 会发送失败/重试。

预期收到类似：

```text
t0AA8 0807060504030201
```

### 方向 2：CANable → T-2Can

```powershell
python examples\slcan_test.py --port COM4 --bitrate 500000 --id 0x123 --data 1122334455667788 --period 1 --count 10
```

然后在 T-2Can 的网页日志里看：

1. 电脑/手机连 WiFi `T-2Can_xxxx`，密码 `12345678`；
2. 打开 <http://192.168.4.1/log>；
3. 看到 `can a received data`、`can a receive id: 0x123` 和 8 个数据字节，就说明 CANable 发、T-2Can 收成功。

如果网页日志不方便，也可以烧 `examples/can` 或自己写一个只打印 CAN A 的固件。



- slcan 固件**不对配置命令返回 ACK/NACK**，只有 `V`、`E` 和收到的 CAN 帧会回数据。
- `E=0` 只代表固件层没有发送失败，**不代表总线上一定有节点 ACK**。
- 要验证对方真的收到，需要总线上至少有一个同波特率的活动节点，或者用第二块 CAN 分析仪。
- 无 ACK 时脚本会先发 `A0` 关闭自动重传，只尝试发一次，避免总线被反复重发拖住。

## 实测记录

2026-10-18，BYZT CANable 2.0（slcan）：

```text
port=COM4  USB ID=16D0:117E
V = 16e7497-dirty github.com/normaldotcom/canable2.git
E = 0
listen 2s @500k: 无总线报文
TX = t7FE81122334455667788
after TX E = 0
```

说明串口协议和发送路径正常；因为当时总线上没有其他节点，未验证 ACK。
