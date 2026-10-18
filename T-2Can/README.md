# T-2Can（LILYGO）资料与说明

本目录是 [Xinyuan-LilyGO/T-2Can](https://github.com/Xinyuan-LilyGO/T-2Can) 的**精简归档**：
只保留原理图、MCP2515 数据手册、关键例程和接线/测试说明。上游仓库里的 70 MB 固件、3D 模型没有重复上传。

上游仓库：<https://github.com/Xinyuan-LilyGO/T-2Can>
许可证：GPL 3.0（见 [LICENSE](LICENSE)）

## 1. 这是什么

LILYGO T-2Can 是一块 **ESP32-S3 双路 CAN 开发板**，不是 CANable 那种即插即用的 USB-CAN 棒。

| 版本 | CAN A 控制器 | CAN 类型 |
|---|---|---|
| **T-2Can_V1.0** | MCP2515（SPI） | 经典 CAN 2.0 |
| **T-2Can-Fd_V1.0** | MCP2518FD（SPI） | 经典 CAN + CAN FD |

两路 CAN：

- **CAN A**：ESP32-S3 通过 SPI 接 MCP2515 / MCP2518FD；
- **CAN B**：ESP32-S3 内置 TWAI 控制器 + 外部隔离收发器。

> 本项目实际使用的是 **T-2Can_V1.0（MCP2515）**，所以只有经典 CAN，没有 FD。

## 2. 硬件要点

| 项目 | 内容 |
|---|---|
| MCU | ESP32-S3-WROOM-1U，16 MB Flash / 8 MB PSRAM |
| 隔离 | 两路 TD501MCAN 隔离 CAN 收发模块（2.5 kV） |
| 终端电阻 | 每路板载 120Ω，带 TVS、共模电感、自恢复保险丝 |
| 供电 | USB-C 5V，或 2Pin 电源端子（标 +24V/GND，12V 也可） |
| 接口 | USB-C、UART、BOOT-0、两路 4Pin CAN 端子 |
| 尺寸模型 | 上游 `structure/`，本目录未收录 |

### 引脚

```text
CAN A (SPI):  CS=10  SCLK=12  MOSI=11  MISO=13
              MCP2515: RST=9  INT=8
              MCP2518: INT=8/9/3
CAN B (TWAI): TX=7   RX=6
BOOT:         IO0
```

详见 [examples/pin_config.h](examples/pin_config.h)。

### CAN 端子

每路 4Pin：`CANH` / `CANL` / `SGND` / `DGND`。

- `SGND` 是隔离 CAN 侧地，接另一个非隔离节点（如 CANable）时，把对方 GND 接到 `SGND`；
- `DGND` 是数字侧地，做 CAN 总线参考时用 `SGND`；
- **不要把 12V/24V 接到 CAN 端子**。

## 3. 出厂固件行为（original_test）

出厂固件 `examples/original_test.ino`：

- 上电先开 WiFi AP `T-2Can_xxxx`，密码 `12345678`，同时尝试连接代码里写死的两个 WiFi；
- 起 Web 服务器：`/`、`/log`、`/clear`；
- WiFi 初始化最多会等约 **40 秒**，之后才初始化 CAN；
- 之后每 **3 秒** 轮流发一帧（即每个通道每 6 秒一帧）：

| 通道 | ID | DLC | 数据 |
|---|---|---|---|
| CAN A | `0xAA` | 8 | `08 07 06 05 04 03 02 01` |
| CAN B | `0xBB` | 8 | `01 02 03 04 05 06 07 08` |

- 收到 CAN A 的帧会打印到串口和网页日志；
- CAN B 没接节点时，日志里出现 `can b: Failed to queue message for transmission` 是正常的；
- 串口日志：USB 端是 `COM5`（ESP32-S3 USB JTAG/serial），波特率 115200；板上 UART 排针是 UART0。

## 4. 编译和烧录

### PlatformIO

```bash
cd T-2Can
# 修改 platformio.ini:
#   default_envs = can            # CAN A + CAN B 收发示例
#   default_envs = esp32_can      # 只用内置 TWAI
#   default_envs = original_test  # 出厂固件
pio run -t upload
```

### Arduino

1. 打开 `examples/can/can.ino`；
2. 开发板选 `ESP32S3 Dev Module`；
3. Flash Size 16MB，PSRAM 选 `OPI PSRAM`；
4. USB CDC On Boot、USB Mode 按上游 README 设置；
5. 编译上传。

### 预编译固件

上游 `firmware/` 里有 T-2Can 和 T-2Can-Fd 的出厂固件（最新 `202607170958`），
用乐鑫 Flash Download Tool 烧录；失败时按住 BOOT-0 再上电。

## 5. CAN FD 版本的注意点

T-2Can-Fd 的控制器是 **MCP2518FD**，但原理图上两路隔离收发器仍标 **TD501MCAN**。
金升阳 TD501MCAN 规格最高 **1 Mbps**，不是 CAN FD 收发器。

因此如果实物也是 TD501MCAN：

- 经典 CAN 没问题；
- FD 数据段 5M 很可能被收发器限制，实际只能低速 FD 或经典 CAN。

需要真正 5M FD 时，要确认实物收发器型号，必要时换 ISO1042、TJA1051T-3 等 FD 收发器。

## 6. 本目录内容

```text
T-2Can/
├── README.md                     本文件
├── CANABLE-T2CAN-TEST.md         CANable ↔ T-2Can 接线和双向收发测试记录
├── LICENSE                       GPL 3.0
├── hardware/
│   ├── T-2Can_V1.0-schematic.pdf 原理图
│   └── MCP2515-datasheet.pdf     MCP2515 数据手册
└── examples/
    ├── can.ino                   CAN A + CAN B 收发示例
    ├── original_test.ino         出厂固件源码
    └── pin_config.h              引脚定义
```

固件、3D 模型等大文件请到上游仓库或 Releases 下载。
