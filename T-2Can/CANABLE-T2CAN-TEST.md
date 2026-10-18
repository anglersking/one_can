# CANable ↔ T-2Can 双向收发测试

验证目标：CANable 2.0（slcan）和 T-2Can_V1.0（MCP2515）在同一条 500 kbit/s 经典 CAN 总线上互相收发。

## 1. 接线

T-2Can 使用 **CAN A（P2 端子，MCP2515）**：

| CANable | T-2Can P2（CAN A） |
|---|---|
| `CAN_H` | `CANHA` |
| `CAN_L` | `CANLA` |
| `GND` | `SGNDA`（隔离侧地） |

- 两边都设 **500 kbit/s**；
- T-2Can 用 USB-C 供电即可，不需要 12V/24V；
- 断电测 `CAN_H`-`CAN_L`，约 **60Ω** 说明两端各有一个 120Ω；只有 120Ω 时把 CANable 的 P2 终端跳线接上；
- 不要把 12V 接到 CAN 端子。

## 2. 哪个节点发什么

### CANable（slcan，PC 端）

测试时发送：

```text
ID   = 0x123
DLC  = 8
数据 = 11 22 33 44 55 66 77 88
周期 = 1 秒
次数 = 5
```

对应 slcan 命令：

```text
t12381122334455667788
```

### T-2Can 出厂固件（original_test）

每 3 秒轮流发一帧，即每个通道每 6 秒一帧：

| 通道 | ID | DLC | 数据 |
|---|---|---|---|
| CAN A | `0xAA` | 8 | `08 07 06 05 04 03 02 01` |
| CAN B | `0xBB` | 8 | `01 02 03 04 05 06 07 08` |

- 本次只接了 CAN A，所以 CANable 只应该收到 `0xAA`；
- T-2Can 的 CAN B 没接节点，日志里 `Failed to queue message` 是正常的。

## 3. 测试命令

### 方向 1：T-2Can → CANable

```powershell
python examples\slcan_test.py --port COM4 --bitrate 500000 --listen-normal 20
```

必须用 `--listen-normal`，它是正常模式，会 ACK 对方。
`--listen` 是静默模式，不 ACK，T-2Can 可能发送失败/重试。

### 方向 2：CANable → T-2Can

```powershell
python examples\slcan_test.py --port COM4 --bitrate 500000 --id 0x123 --data 1122334455667788 --period 1 --count 5
```

同时读 T-2Can 串口（COM5，115200）或打开网页日志 <http://192.168.4.1/log>。

## 4. 实测结果（2026-10-18）

设备：

```text
CANable: COM4, USB 16D0:117E, 固件 V=16e7497-dirty
T-2Can:  COM5, USB 303A:1001
```

### T-2Can → CANable

CANable 在 20 秒内收到 3 帧：

```text
t0AA80807060504030201
t0AA80807060504030201
t0AA80807060504030201
```

解析：

```text
t      标准数据帧
0AA    ID = 0xAA
8      DLC = 8
0807060504030201  数据
```

与 T-2Can 出厂固件 CAN A 的发送内容一致。

### CANable → T-2Can

T-2Can 串口日志：

```text
can a received data
can a receive id: 0x123
can a receive data length: 8
can a receive data [0]: 17
can a receive data [1]: 34
can a receive data [2]: 51
can a receive data [3]: 68
can a receive data [4]: 85
can a receive data [5]: 102
can a receive data [6]: 119
can a receive data [7]: 136
```

T-2Can 打印的是**十进制**，换算成十六进制正好是：

```text
17  -> 0x11
34  -> 0x22
51  -> 0x33
68  -> 0x44
85  -> 0x55
102 -> 0x66
119 -> 0x77
136 -> 0x88
```

与 CANable 发送的 `11 22 33 44 55 66 77 88` 一致。

## 5. 结论

- 接线、共地、500k 波特率、60Ω 终端都正确；
- CANable 发、T-2Can 收：通过；
- T-2Can 发、CANable 收：通过；
- 两个节点都可以作为对方的 ACK 节点，适合后续做 7 个电机节点的总线预研。

## 6. 常见问题

| 现象 | 检查 |
|---|---|
| CANable 收不到 0xAA | T-2Can 上电后等 40 秒（WiFi 初始化）；确认接的是 P2 CAN A；确认 500k |
| T-2Can 收不到 0x123 | 确认 CANable 用正常模式发送；检查 `CAN_H/L` 是否接反；检查 `SGNDA` 共地 |
| 日志里 `can b: Failed to queue` | CAN B 没接节点，正常，不影响 CAN A |
| 一发就错误/丢帧 | 终端电阻不是 60Ω；线太长；两边波特率不一致 |
| COM 口号变了 | 设备管理器重新确认；T-2Can 是 ESP32-S3 USB JTAG/serial，CANable 是 16D0:117E |
