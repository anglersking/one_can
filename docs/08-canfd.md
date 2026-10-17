# 08 - CAN FD 支持分析与实测

先给结论：

> **这块板子的 MCU 支持 CAN FD，slcan 固件也实现了 CAN FD 命令，数据段可选 2 Mbit/s / 5 Mbit/s。**
> **但 candleLight 固件不支持 FD；最终能不能稳定跑，还取决于板上 CAN 收发器是 TJA1050 还是 TJA1051T-3。**

## 1. 分四层看

| 层 | 本包情况 | 结论 |
|---|---|---|
| **MCU** | STM32G431CBT6，片内 FDCAN1，`src/can.c` 里用的就是 `FDCAN_FRAME_FD_BRS` | ✅ 支持 |
| **固件** | slcan `b158aa7`：源码 README 明确写了 CANFD 命令和 `Y2`/`Y5` 数据段 | ✅ 支持，beta |
| **固件** | candleLight `ba6b1dd`：包内没有源码/说明，官方 CANable 2.0 的 candlelight 不支持 FD | ❌ 不支持 |
| **收发器** | 原理图 U4 标注 `TJA1050` / `TJA1051T-3` 两种 | ⚠️ 看实物 |
| **上位机** | cangaroo 支持 slcan FD；TSMaster/BUSMASTER 走 candleLight | ⚠️ 选对软件 |
| **脚本** | python-can 的 slcan 后端不支持 FD | ❌ 不支持 |

任何一层是 ❌，整条链路就跑不了 FD。

## 2. 收发器是最大的坑

原理图 U4 位号同时写了两个型号：

| 型号 | 供电 | 数据手册最高速率 | FD |
|---|---|---|---|
| `TJA1050` | 5 V | 1 Mbit/s | ❌ 不是 FD 收发器 |
| `TJA1051T-3` | 3.3 V | 5 Mbit/s | ✅ 支持 CAN FD |

- 图纸中 U4 的 VCC 默认接 **5V**，默认 BOM 更像 TJA1050。
- 图纸另外画了 `3V3-CAN`（Q1/Q2 开关 + 22 µF），是给 3.3V 收发器预留的。
- **拿到板子先看 U4 丝印**：
  - `TJA1050` → 只跑经典 CAN（≤1 Mbit/s），不要开 FD；
  - `TJA1051T-3`（或其它 FD 收发器）→ 可以试 2M/5M。

为什么 TJA1050 不行：CAN FD 的数据段靠收发器环路延迟对称性保证采样，TJA1050 的数据手册没有 FD 指标，2M 以上容易出错帧。有人短距离、低速率“能用”，但不可靠。

## 3. slcan 固件的 FD 命令

配置命令必须在 `O`（打开通道）之前发送：

| 命令 | 作用 |
|---|---|
| `S6` | 仲裁段 500 kbit/s（其它见 04 文档的 `-s` 表） |
| `Y2` | 数据段 2 Mbit/s（默认） |
| `Y5` | 数据段 5 Mbit/s |
| `O` | 打开通道 |
| `C` | 关闭通道 |
| `V` | 返回固件版本 |
| `E` | 返回错误寄存器 |

发送帧的前缀：

| 前缀 | 帧类型 | ID 长度 | BRS |
|---|---|---|---|
| `t` | 经典 CAN 数据帧 | 11 位（3 hex） | - |
| `T` | 经典 CAN 数据帧 | 29 位（8 hex） | - |
| `r` / `R` | 经典 CAN 远程帧 | 11 / 29 位 | - |
| `d` | CAN FD 数据帧 | 11 位 | 关 |
| `D` | CAN FD 数据帧 | 29 位 | 关 |
| `b` | CAN FD 数据帧 | 11 位 | **开** |
| `B` | CAN FD 数据帧 | 29 位 | **开** |

DLC 编码（FD 最大 64 字节）：

| DLC 字符 | 字节数 |
|---|---|
| `0`–`8` | 0–8 |
| `9` | 12 |
| `A` | 16 |
| `B` | 20 |
| `C` | 24 |
| `D` | 32 |
| `E` | 48 |
| `F` | 64 |

### 例子

```text
b1239112233445566778899AABB
│└┬┘│└──────────┬──────────┘
│ │  │           └ 12 字节数据
│ │  └ DLC=9 → 12 字节
│ └── 标准 ID = 0x123
└──── FD + BRS，标准帧
```

- 扩展帧：`B000001239112233445566778899AABB`（ID=`0x00000123`，DLC=9，12 字节）
- FD 不带 BRS：`d1238AABBCCDDEEFF`（8 字节）
- 经典帧：`t12381122334455667788`

> 本固件 **不对配置命令返回 ACK/NACK**，不要等 `\r`；只有 `V`、`E` 和收到的 CAN 帧会回数据。
> 收到的 FD 帧会以 `b/B`（带 BRS）或 `d/D`（不带 BRS）开头回传。

## 4. 用 cangaroo 测 FD

1. 烧 **slcan** 固件（candleLight 不行）。
2. 打开 cangaroo → `Measurement → Start Measurement`。
3. `Interfaces` 选 COM 口；
   `Bitrate` = `500000`；
   `CanFD Bitrate` = `2000000`（或 `5000000`）。
4. 发送帧时选：
   - `FD` 帧；
   - `BRS` 打开（对应 `b`/`B` 命令）；
   - `DLC` 按实际长度选（9–F 对应 12–64 字节）。
5. 总线上至少要有另一个 FD 节点，否则没有 ACK，发送会失败/重试。

## 5. 用串口助手手工测

1. 串口助手打开 `COMx`，115200 8N1（CDC 波特率无所谓）。
2. 依次发送（每行末尾加 `\r`）：

   ```text
   V         → 返回 b158aa7 ...
   S6        → 500 kbit/s
   Y2        → 数据段 2 Mbit/s
   O         → 打开
   b1239112233445566778899AABB
   ```

3. 如果总线另一端有 FD 节点，应该能收到它发的帧；收到的帧以 `b`/`B`/`d`/`D` 开头。
4. 测试完发 `C` 关闭。

## 6. 限制与注意事项

- **beta**：原厂对 slcan FD 的定位就是 beta（2M/5M），不建议直接上量产。
- **无 ACK/NACK**：串口层没有命令确认，出错只能靠 `E` 错误寄存器和总线行为判断。
- **DLC 固定映射**：9–F 只能选标准 FD 长度，不能任意长度。
- **数据段只有 2M/5M 两档**（`Y2`/`Y5`），没有 1M/4M/8M 选项。
- **经典 CAN 节点会报错**：FD 帧在经典 CAN 节点看来是错误帧，混合总线要么全 FD，要么关掉 BRS/只用经典帧。
- **USB CDC 吞吐**：64 字节 FD 帧 + 文本编码，总线负载高时可能丢帧/延迟，大批量数据建议 candlelight（但 candlelight 没 FD）或换专用分析仪。
- **线材与终端**：5 Mbit/s 数据段对线长、终端、支线很敏感，桌面上尽量 <0.5 m，两端 120Ω。

## 7. 想要 candleLight + FD？

本包的 candlelight `ba6b1dd` 不支持 FD，且上游 candleLight_fw 主线不支持 STM32G431。
如果要 Linux 原生 SocketCAN + FD，需要第三方固件，例如 Elmue 的 **CANable 2.5**（Slcan + Candlelight，G431，支持 FD，宣称测到 10 Mbaud）：

- <https://github.com/Elmue/CANable-2.5-firmware-Slcan-and-Candlelight>

注意：这是第三方固件，烧录前确认板子的晶振/引脚/收发器与固件匹配，刷错可能不启动；不属于本资料包的内容。

## 8. 上板测试清单

- [ ] U4 丝印是 `TJA1051T-3` 或同级 FD 收发器
- [ ] 固件是 slcan `b158aa7`
- [ ] cangaroo 里 Bitrate=500k，CanFD Bitrate=2M/5M
- [ ] 总线上有第二个 FD 节点
- [ ] 终端电阻正确（两端 120Ω）
- [ ] CAN_H/CAN_L 没接反，共地
- [ ] 先发经典帧确认链路，再发 FD 帧
- [ ] 出错时读 `E` 错误寄存器，并 `ip -details link show can0`（Linux）或 cangaroo 的错误计数
