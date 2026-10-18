# ESP32-S3 + 野火小智 CAN 收发器模块（经典 CAN）

这个组合可以正常跑经典 CAN：ESP32-S3 内部有 **TWAI** 控制器，野火模块只是 **SIT1042AQT/3 收发器**，两者正好配套。

> 只支持经典 CAN。ESP32-S3 的 TWAI 不支持 CAN FD，虽然 SIT1042 芯片本身支持到 5 Mbps FD。

## 1. 接线

| 野火模块 | ESP32-S3 / 总线 | 说明 |
|---|---|---|
| `EN` | **3.3V** | **必须接 3.3V**，决定 RXD/TXD 电平 |
| `5V` | **5V** | 模块供电，不要接 3.3V |
| `GND` | **GND** | 共地 |
| `TXD` | **GPIO4** | ESP32 的 CAN_TX |
| `RXD` | **GPIO5** | ESP32 的 CAN_RX |
| `CANH` | 总线 CAN_H | |
| `CANL` | 总线 CAN_L | |
| `GND`（CAN 端子） | 总线 GND | 和 CANable 共地 |

> **EN 接 5V 会让 RXD 输出 5V，ESP32-S3 GPIO 不耐 5V，会损坏。必须接 3.3V。**

模块 5Pin 排针定义（官方）：

```text
1 EN    收发器 I/O 电平选择，接 3V3
2 5V    电源 5V
3 GND   地
4 TXD   MCU -> 模块
5 RXD   模块 -> MCU
```

## 2. 终端电阻

- 模块上的 `SW1` 是 120Ω 投入开关，默认关闭；
- 和 CANable 两点一线测试时：模块 `SW1` 打开，CANable 的 P2 跳线接上；
- 断电测 `CAN_H`-`CAN_L` 应约 **60Ω**。

## 3. 测试代码

[`esp32s3_can_test.ino`](esp32s3_can_test.ino)：

- 500 kbit/s；
- 每秒发一帧 `0x123`，8 字节 `01..08`；
- 同时接收并打印总线上的帧；
- 串口 115200。

Arduino IDE 设置：

```text
Board:            ESP32S3 Dev Module
Flash Size:       按你的板子选（常见 16MB）
PSRAM:            按你的板子选
USB CDC On Boot:  Enabled（如果你想用 USB-C 看串口）
Upload Speed:     921600
```

如果板子没有 USB CDC，串口日志从 UART0 输出，接 USB-TTL 到 TX/RX 即可。

## 4. 和 CANable 互测

### 方向 1：ESP32-S3 → CANable

1. ESP32-S3 烧好代码，接好模块和 CANable；
2. Windows 运行：

   ```powershell
   python examples\slcan_test.py --port COM4 --bitrate 500000 --listen-normal 20
   ```

3. 预期收到：

   ```text
   t12380102030405060708
   ```

### 方向 2：CANable → ESP32-S3

```powershell
python examples\slcan_test.py --port COM4 --bitrate 500000 --id 0x7FE --data 1122334455667788 --period 1 --count 5
```

ESP32-S3 串口应打印：

```text
RX id=0x7FE dlc=8 data=11 22 33 44 55 66 77 88
```

## 5. 没有第二个节点时自测

把 `TWAI_MODE_NORMAL` 改成 `TWAI_MODE_NO_ACK`，可以在没有 ACK 的情况下发送（自测用）。
正常接总线时必须用 `TWAI_MODE_NORMAL`，否则不会 ACK 其他节点，可能导致对方发送失败。

## 6. 常见问题

| 现象 | 检查 |
|---|---|
| ESP32 串口没有输出 | USB CDC On Boot 设置；或改用 UART0 |
| CANable 收不到 | EN 是否接 3.3V；CANH/L 是否接反；模块 SW1 和 CANable 终端是否打开 |
| ESP32 发不出去 | 总线上没有第二个节点 ACK；先用 CANable 正常模式监听，或临时用 `TWAI_MODE_NO_ACK` |
| ESP32 收到乱码/错误 | 两边波特率不一致；线太长；终端电阻不对 |
| GPIO4/5 被占用 | 换其它可用 GPIO，代码里改 `CAN_TX`/`CAN_RX` |
| 想跑 CAN FD | ESP32-S3 不支持，换 STM32G431 / T-2Can FD 等带 FDCAN 的 MCU |
