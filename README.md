# one_can

CANable 2.0（BYZT 兼容板）USB-CAN / CAN-FD 适配器的资料归档与使用笔记。

> 项目背景：一个 CAN 通信模块，用于验证，后面用于机器人关节电机驱动项目。

原始资料是 `BYZT-CANable2.0资料.zip`（1.19 GB）。仓库里只保留**文档、原理图、固件、截图和 Python 示例**（约 4 MB）；
原包里的第三方安装包、编译器、源码压缩包（约 1.17 GB）放在 GitHub Releases：

> **下载地址：** <https://github.com/anglersking/one_can/releases/tag/v1.0-resources>
>
> 完整清单和说明见 [`RESOURCES.md`](RESOURCES.md)。

这样 `git clone` 只有几 MB，需要装工具时再去 Release 页面单独下载。

根目录的 `docs/` 是我根据包内资料整理的使用笔记，方便快速上手；原始说明在
[`BYZT-CANable2.0资料/`](BYZT-CANable2.0资料/) 里也能找到。

---

## 一、先看结论

| 问题 | 结论 |
|---|---|
| 这是什么 | STM32G431 的 USB 转 CAN 适配器，CANable 2.0 兼容板，Type-C 接口，带 120Ω 终端电阻跳线 |
| 能当 USB-CAN 用吗 | 能。默认烧 **slcan** 固件，Win10/11 免驱，枚举成串口 `COMx` |
| **支持 CAN FD 吗** | **MCU 和 slcan 固件支持（beta，数据段 2 Mbit/s 或 5 Mbit/s）；candleLight 固件不支持 FD；实际能不能跑还取决于板上收发器型号** |
| 支持 PCAN 吗 | 不支持。没有 PCAN 固件，PCAN-View / PCAN-Basic 用不了 |
| Windows 推荐方案 | slcan 固件 + [cangaroo](https://github.com/HubertD/cangaroo/releases) |
| Linux 推荐方案 | candleLight 固件（原生 `can0`）或 slcan + `slcand` |
| 要 CAN FD 用什么 | **slcan 固件 + 支持 slcan FD 的上位机（cangaroo）**，不要用 candleLight |

> ⚠️ **CAN FD 的关键坑**：原理图上收发器位号 U4 同时标注了 `TJA1050` 和 `TJA1051T-3`。
> `TJA1050` 是 5V、最高 1 Mbit/s 的经典 CAN 收发器，**不能可靠跑 FD 数据段**；
> `TJA1051T-3` 才是 3.3V、支持 CAN FD（最高 5 Mbit/s）的型号。**以实物丝印/购买型号为准。**
> 详细分析见 [docs/08-canfd.md](docs/08-canfd.md)。

---

## 二、5 分钟上手

### Windows（默认 slcan 固件）

1. 用 Type-C 数据线把板子接到电脑（不是只能充电的线）。
2. 打开“设备管理器 → 端口”，应出现 **USB 串行设备 (COMx)**；Win10/11 不需要装驱动。
3. 下载 [cangaroo](https://github.com/HubertD/cangaroo/releases)，解压运行 `cangaroo.exe`。
4. 菜单 `Measurement → Start Measurement`。
5. 在弹出的 `Network1` 窗口：
   - `Interfaces` 里选中对应的 COM 口；
   - `Bitrate` 设为 `500000`（经典 CAN 仲裁段）；
   - 需要 FD 时 `CanFD Bitrate` 设为 `2000000`（或 `5000000`）；
   - 需要解析报文可在 `Can Databases` 里加载 DBC。
6. 点 `OK`，即可收发。发送时注意选对 `DLC`。

对应原始说明：[docs/02-windows-quickstart.md](docs/02-windows-quickstart.md)

### Linux（candleLight 固件）

```bash
sudo apt install can-utils
sudo ip link set can0 up type can bitrate 500000
candump can0
cansend can0 123#1122334455667788
```

如果是 slcan 固件，则先映射成 can0：

```bash
sudo slcand -o -c -s6 /dev/ttyACM0 can0   # -s6 = 500 kbit/s
sudo ifconfig can0 up
```

详见 [docs/04-linux-socketcan.md](docs/04-linux-socketcan.md)。

### Python（经典 CAN）

```bash
pip install python-can
```

```python
import can

bus = can.interface.Bus(bustype="slcan", channel="COM4", bitrate=500000)
bus.send(can.Message(arbitration_id=0x123, data=[1, 2, 3, 4], is_extended_id=False))
```

示例见 [`BYZT-CANable2.0资料/09-Python-can使用/`](BYZT-CANable2.0资料/09-Python-can使用/)。注意：**python-can 的 slcan 后端不支持 CAN FD**。

要直接发 slcan 帧、监听总线或测试 CAN FD，用实测过的脚本：

```bash
pip install pyserial
python examples/slcan_test.py --port COM4 --bitrate 500000 --id 0x7FE --data 1122334455667788
python examples/slcan_test.py --port COM4 --bitrate 500000 --listen 3
```

详见 [`examples/README.md`](examples/README.md)。

### T-2Can（MCP2515）作为第二个节点

T-2Can 的 **CAN A（P2 端子，MCP2515）** 可以和 CANable 直接互测，500 kbit/s：

- 接线：`CAN_H→CANHA`、`CAN_L→CANLA`、`GND→SGNDA`；
- CANable 收：`python examples/slcan_test.py --port COM4 --bitrate 500000 --listen-normal 20`
- CANable 发：`python examples/slcan_test.py --port COM4 --bitrate 500000 --id 0x123 --data 1122334455667788 --period 1 --count 5`

T-2Can 出厂固件在 CAN A 上发 `0xAA`（8 字节 `08 07 06 05 04 03 02 01`），每 6 秒一帧；
CAN B 上发 `0xBB`，本次未接。

- T-2Can 资料与硬件说明：[`T-2Can/README.md`](T-2Can/README.md)
- 接线、实测日志、哪个节点发什么：[`T-2Can/CANABLE-T2CAN-TEST.md`](T-2Can/CANABLE-T2CAN-TEST.md)

### 一条总线带 7 个无刷电机

**够。** 7 个节点对 CAN 来说很少，关键是控制周期和总线负载：

- 100–200 Hz：500 kbit/s 经典 CAN 够用（命令+反馈约 35–70% 负载）；
- 500 Hz–1 kHz：建议 1 Mbit/s，并压缩 PDO 数量/数据长度；
- 1 kHz 以上或每个电机传大量数据：考虑 CAN FD 或双总线；
- 目标负载控制在 50–60% 以内，终端电阻、支线长度、共地/隔离比节点数量更重要。

完整计算见 [`docs/10-seven-motors.md`](docs/10-seven-motors.md)。

---

## 三、两种固件怎么选

| | **slcan**（出厂默认） | **candleLight** |
|---|---|---|
| 电脑识别成 | USB 串口 `COMx` / `/dev/ttyACMx` | USB 设备（gs_usb） |
| Windows | 免驱，串口工具直接用 | 需要 WinUSB 驱动（Win7 用 Zadig） |
| Linux | `slcand` 映射为 `can0` | 内核原生 `can0`，不用 slcand |
| 上位机 | cangaroo、串口工具、自定义脚本 | cangaroo、TSMaster、BUSMASTER、cantact |
| **CAN FD** | **支持（beta，2M/5M）** | **不支持** |
| 性能 | 受 USB CDC 串口限制 | 吞吐更高、延迟更低 |
| 本仓库文件 | `03-固件/slcan/` | `03-固件/candlelight/` |

**建议**：先不折腾，slcan + cangaroo 完成 90% 的调试；只有在 Linux 上要原生 SocketCAN 或高吞吐时才换 candleLight。

---

## 四、CAN FD 支持情况（重点）

分四层看，任何一层不支持都用不了 FD：

| 层 | 情况 | 结论 |
|---|---|---|
| MCU | STM32G431CBT6，片内 FDCAN1（PB8/PB9） | ✅ 硬件支持 |
| 固件 | slcan `b158aa7`：实现非标准 slcan FD 命令（`Y2`/`Y5`、`d/D/b/B` 帧） | ✅ 支持，beta |
| 固件 | candleLight `ba6b1dd`：canable.io 明确说明 CANable 2.0 的 candlelight 不支持 FD | ❌ 不支持 |
| 收发器 | TJA1050（5V，1 Mbit/s，非 FD） / TJA1051T-3（3.3V，FD 5 Mbit/s） | ⚠️ 看实物 |
| 上位机 | cangaroo 支持 slcan FD；TSMaster/BUSMASTER 只支持 candlelight（本包说明） | ⚠️ 选对软件 |
| 脚本 | python-can 的 slcan 后端不支持 FD | ❌ 不支持 |

**slcan FD 命令速查**（配置命令必须在 `O` 之前发）：

```text
S6        仲裁段 500 kbit/s
Y2        数据段 2 Mbit/s（默认）
Y5        数据段 5 Mbit/s
O         打开通道
b1239112233445566778899AABB     FD + BRS，标准帧，12 字节（DLC=9）
B000001239112233445566778899AABB FD + BRS，扩展帧
d1238AABBCCDDEEFF               FD 不带 BRS
C         关闭通道
```

DLC 编码：`9=12`、`A=16`、`B=20`、`C=24`、`D=32`、`E=48`、`F=64` 字节。

完整说明、实测步骤和限制见 **[docs/08-canfd.md](docs/08-canfd.md)**。

---

## 五、仓库结构

```text
.
├── README.md
├── docs/                              整理的使用笔记
│   ├── 01-hardware.md                 硬件规格、接口、原理图要点
│   ├── 02-windows-quickstart.md       Windows + cangaroo 上手
│   ├── 03-firmware-flashing.md        固件烧录（ST-LINK / DFU 网页 / DfuSe）
│   ├── 04-linux-socketcan.md          Linux / 嵌入式 SocketCAN
│   ├── 05-python-can.md               python-can 示例与限制
│   ├── 06-build-firmware.md           从源码编译固件
│   ├── 07-win7.md                     Win7 下装驱动
│   ├── 08-canfd.md                    CAN FD 支持分析 + 实测方法
│   ├── 09-faq.md                      常见问题
│   ├── 10-seven-motors.md             一条 CAN 总线带 7 个无刷电机的带宽分析
│   ├── images/                        烧录、Win7 配置截图
│   └── original-package-inventory.md  原始压缩包文件清单
├── examples/                          实测可用的 slcan 发送/监听脚本
│   ├── slcan_test.py
│   └── README.md
├── T-2Can/                            LILYGO T-2Can 资料、原理图、互测记录
│   ├── README.md
│   ├── CANABLE-T2CAN-TEST.md
│   ├── hardware/
│   └── examples/
├── BYZT-CANable2.0资料/               原包中的文档、原理图、固件、截图、示例
│   ├── 01-原理图/
│   ├── 02-源码/                       编译说明（源码包在 Releases）
│   ├── 03-固件/
│   ├── 04-烧录驱动及工具/              下载说明（安装包在 Releases）
│   ├── 05-应用软件/                    下载说明（安装包在 Releases）
│   ├── 06-Linux(SocketCAN)或者嵌入式上使用/
│   ├── 07-固件烧录/
│   ├── 08-WIN7下使用说明/              截图 + 下载说明（Zadig 在 Releases）
│   ├── 09-Python-can使用/
│   └── 使用说明.txt
├── RESOURCES.md                       Release 附件清单（1.17 GB 大文件）
```

各目录的用途：

- 只想赶快通起来：看 `docs/02-windows-quickstart.md`。
- 怀疑硬件/接线：看 `docs/01-hardware.md` 和 `BYZT-CANable2.0资料/01-原理图/` 里的原理图。
- 想用 CAN FD：先看 `docs/08-canfd.md`，确认收发器型号。
- 固件刷坏了：看 `docs/03-firmware-flashing.md`，优先 ST-LINK。
- 要在 Linux/机器人控制器上用：看 `docs/04-linux-socketcan.md`。
- 想改固件：看 `docs/06-build-firmware.md`，源码压缩包在 Releases。

---

## 六、固件与烧录

固件在 `BYZT-CANable2.0资料/03-固件/`：

| 文件 | 用途 |
|---|---|
| `slcan/canable2-b158aa7.bin` | ST-LINK / CubeProgrammer 烧到 `0x08000000` |
| `slcan/canable2-b158aa7.dfu` | DfuSe Demo / 网页 DFU 烧录 |
| `candlelight/canable2_fw-ba6b1dd.bin` | ST-LINK 烧录 |
| `candlelight/canable2_fw-ba6b1dd.dfu` | DfuSe Demo / 网页 DFU 烧录 |
| `candlelight/canable2-testing.bin` | 测试固件，正常使用不需要 |

三种烧录方式（详细步骤 + 截图见 [docs/03-firmware-flashing.md](docs/03-firmware-flashing.md)）：

1. **ST-LINK（最稳，推荐）**：SWD 口接 `3V3 / SWDIO / SWCLK / GND`，用 STM32CubeProgrammer 或 ST-LINK Utility 烧 `.bin`。
2. **网页 DFU**：短接 BOOT0 上电 → 设备出现 `DFU in FS Mode` → 打开 <https://canable.io/updater/canable2.html> → Connect and Update。
3. **DfuSe Demo**：短接 BOOT0 → 装 ST 的 DFU 驱动 → 选 `.dfu` → Upgrade。

小技巧：已经正常使用的板子，**拔出后 1 秒内重新插入**会自动进入 DFU；正常使用时拔出后等 3 秒再插。

---

## 七、大文件下载（Releases）

原包里的第三方安装包、编译器和源码压缩包放在 GitHub Releases，不进入 git 历史：

> <https://github.com/anglersking/one_can/releases/tag/v1.0-resources>

| 文件 | 大小 |
|---|---:|
| `TSMaster.zip` | 347.1 MB |
| `STM32CubeProgrammer win64/win32` | 217.6 / 216.1 MB |
| `gcc-arm-none-eabi-5_4-...linux.tar.bz2` | 88.3 MB |
| `jre-8u291-windows-x64/i586.exe` | 80.7 / 70.3 MB |
| `BUSMASTER_Installer_Ver_3.2.2-cantact.zip` | 42.9 MB |
| `canable2-fw.tar.bz2` | 31.2 MB |
| `STM32 ST-LINK Utility v4.6.0.zip` | 25.4 MB |
| `DfuSe_Demo.rar` | 17.7 MB |
| `cantact-v0.3.0-alpha.zip` | 14.3 MB |
| `cangaroo-win32-ccdcb64.zip` | 12.8 MB |
| `pcan-basic.zip` / `cangaroo-master.zip` | 9.7 / 8.3 MB |
| `ImpulseRC_Driver_Fixer.exe` / `zadig.zip` | 5.8 / 5.3 MB |

完整清单（含原始目录和用途）见 [`RESOURCES.md`](RESOURCES.md)。

官方最新版下载地址：

| 工具 | 地址 |
|---|---|
| TSMaster | <https://www.tosunai.com/> |
| STM32CubeProgrammer | <https://www.st.com/en/development-tools/stm32cubeprog.html> |
| cangaroo | <https://github.com/HubertD/cangaroo/releases> |
| BUSMASTER | <https://github.com/rbei-etas/busmaster> |
| cantact | <https://github.com/linklayer/cantact> |
| canable2-fw 源码 | <https://github.com/normaldotcom/canable2-fw> |


固件源码上游：<https://github.com/normaldotcom/canable2-fw>（本包对应 commit `b158aa7`）。
candleLight 源码上游：<https://github.com/normaldotcom/candleLight_fw/tree/multitarget>（本包对应 `ba6b1dd`，不支持 FD）。

---

## 八、已知坑（先看这一节能省很多时间）

1. **FD 跑不起来**：先确认板上 U4 是 `TJA1051T-3` 而不是 `TJA1050`，再用 slcan 固件 + cangaroo；candleLight 和 python-can 都不支持 FD。
2. **收不到数据**：检查 120Ω 终端电阻跳线（长总线两端各 120Ω，短桌面临时测试可只开一端）、CAN_H/CAN_L 是否接反、是否共地。
3. **设备管理器没有 COM 口**：换一根能传数据的 Type-C 线；Win7 需要装驱动（见 `docs/07-win7.md`）。
4. **进不了 DFU**：短接 BOOT0 再上电；或拔插间隔小于 1 秒；装了 ImpulseRC 驱动后想改用 DfuSe，需要先在设备管理器卸载 `DFU in FS Mode`。
5. **网页烧录后再也连不上网页**：设备变成了 `STM Device in DFU Mode`，卸载它，重新短接 BOOT0 上电，等出现 `DFU in FS Mode`。
6. **串口被占用**：cangaroo 打开 COM 口时，串口助手、TSMaster 等要关掉。
7. **不要用 5V 供电乱接**：CAN 接口只接 CAN_H / CAN_L / GND，板子由 Type-C 供电。

更多见 [docs/09-faq.md](docs/09-faq.md)。

---

## 九、来源与许可

- 原始资料由 BYZT 卖家提供，原理图、固件来自 CANable 开源项目：
  - <https://canable.io/>
  - <https://github.com/normaldotcom/canable2-fw>（GPL）
  - <https://github.com/normaldotcom/candleLight_fw>
- 本仓库中的说明文档是对原始中文资料和公开资料的整理，固件版权归原作者所有。
- 第三方商业工具（TSMaster、STM32CubeProgrammer、DfuSe、JRE 等）未上传，请遵守各自许可。

如果这份资料对你的机器人关节电机项目有帮助，欢迎补充实测记录、CAN FD 抓包和 DBC。
