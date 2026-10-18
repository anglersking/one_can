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

## 重要说明

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
