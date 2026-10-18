# 05 - Python (python-can)

资料包 `09-Python-can使用/` 里有两个示例：

- `can_test.py`
- `python-can.py`

## 1. 安装

```bash
sudo apt update
sudo apt install python3 python3-pip
pip3 install python-can
```

国内网络慢可以换源：

```bash
pip3 install python-can -i https://pypi.tuna.tsinghua.edu.cn/simple
```

检查：

```bash
python3 -c "import can; print(can.__version__)"
```

## 2. 选择正确的后端

| 固件/系统 | bustype | channel | 说明 |
|---|---|---|---|
| slcan + Windows | `slcan` | `COM4` | 串口 |
| slcan + Linux | `slcan` | `/dev/ttyACM0` | 需要 `slcand` 或直接访问串口 |
| candleLight + Linux | `socketcan` | `can0` | 需要先 `ip link set can0 up` |
| candleLight + Windows | `gs_usb`（新版 python-can） | 设备索引 | 需 WinUSB 驱动 |
| PEAK 硬件 | `pcan` | `PCAN_USBBUS1` | **只适用于 PEAK 卡，不适用本板** |

## 3. 发送示例

```python
import can

# Windows + slcan
bus = can.interface.Bus(bustype="slcan", channel="COM4", bitrate=500000)

# Linux + candleLight
# bus = can.interface.Bus(bustype="socketcan", channel="can0", bitrate=500000)

msg = can.Message(
    arbitration_id=0x123,
    data=[0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88],
    is_extended_id=False,
)

try:
    bus.send(msg)
    print("sent:", msg)
except can.CanError as e:
    print("send failed:", e)
```

## 4. 接收示例

```python
import can

bus = can.interface.Bus(bustype="slcan", channel="COM4", bitrate=500000)

for msg in bus:
    print(f"{msg.arbitration_id:03X}  {msg.data.hex(' ')}  dlc={msg.dlc}")
```

## 5. CAN FD 的限制

**python-can 的 `slcan` 后端目前不支持 CAN FD**，原因：

- 标准 slcan 协议没有 FD 帧格式；
- 本固件的 FD 命令（`d/D/b/B`）是厂商扩展，python-can 没有实现；
- `socketcan` 后端本身支持 FD，但 candleLight 固件不支持 FD，所以也用不上。

需要脚本化跑 FD 时：

1. 用 cangaroo 手工验证；
2. 或自己按 [08-canfd.md](08-canfd.md) 的串口协议写一个 Python 封装（`pyserial` + 自定义命令），这是最直接的办法。

## 6. 示例脚本

[`can_test.py`](../BYZT-CANable2.0资料/09-Python-can使用/can_test.py)（原始文件在 `BYZT-CANable2.0资料/09-Python-can使用/`）：

```python
import can

bus = can.interface.Bus(bustype="slcan", channel="COM4", bitrate=500000)
msg = can.Message(arbitration_id=0xc0ffee, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True)
bus.send(msg)
```

直接用 slcan 文本协议（支持 FD、可监听）的实测脚本：

```bash
pip install pyserial
python examples/slcan_test.py --port COM4 --bitrate 500000 --id 0x7FE --data 1122334455667788
```

说明见 [`examples/README.md`](../examples/README.md)。

## 7. 常见错误

| 错误 | 原因 |
|---|---|
| `can.exceptions.CanInitializationError` | COM 口号错/被占用；或 Linux 没起 `can0` |
| `CanOperationError: Failed to transmit` | 总线上没有其他节点 ACK、终端电阻不对 |
| `ImportError: No module named can` | 装到了另一个 Python 环境，用 `python3 -m pip install python-can` |
| `pcan` 打不开 | 本板不是 PEAK 设备，改用 `slcan`/`socketcan` |
| FD 帧发不出 | python-can slcan 不支持，见上文 |
