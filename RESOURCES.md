# 大文件下载（GitHub Releases）

为了控制仓库体积，`one_can` 的 git 历史里**只保留文档、原理图、固件、截图和 Python 示例**（约 4 MB）。
原资料包里的第三方安装包、编译器、源码压缩包都放在 GitHub Releases：

> **下载地址：** <https://github.com/anglersking/one_can/releases/tag/v1.0-resources>

Release 页面里可以直接点文件名下载，不需要登录。所有文件都是原始文件，未做分卷或重新压缩。

## 附件清单

| 文件 | 大小 | 原始目录 | 用途 |
|---|---:|---|---|
| `TSMaster.zip` | 347.1 MB | `05-应用软件/` | 国产 CAN/CANFD 上位机（支持 candleLight） |
| `en.stm32cubeprg-win64-v2-12-0.zip` | 217.6 MB | `04-烧录驱动及工具/` | STM32CubeProgrammer 64 位 |
| `en.stm32cubeprg-win32_v2-12-0.zip` | 216.1 MB | `04-烧录驱动及工具/` | STM32CubeProgrammer 32 位 |
| `gcc-arm-none-eabi-5_4-2016q2-20160622-linux.tar.bz2` | 88.3 MB | `02-源码/` | 编译 canable2-fw 的 ARM 工具链 |
| `jre-8u291-windows-x64.exe` | 80.7 MB | `05-应用软件/cantact/` | cantact 需要的 Java 运行环境（64 位） |
| `jre-8u291-windows-i586.exe` | 70.3 MB | `05-应用软件/cantact/` | cantact 需要的 Java 运行环境（32 位） |
| `BUSMASTER_Installer_Ver_3.2.2-cantact.zip` | 42.9 MB | `05-应用软件/` | 开源 CAN 工具（支持 candleLight） |
| `canable2-fw.tar.bz2` | 31.2 MB | `02-源码/` | slcan 固件源码（commit `b158aa7`，含 .git） |
| `STM32 ST-LINK Utility v4.6.0.zip` | 25.4 MB | `04-烧录驱动及工具/` | ST-LINK 烧录工具（老版本） |
| `DfuSe_Demo.rar` | 17.7 MB | `04-烧录驱动及工具/` | ST 官方 DFU 烧录工具 |
| `cantact-v0.3.0-alpha.zip` | 14.3 MB | `05-应用软件/cantact/` | Java 版 CAN 工具 |
| `cangaroo-win32-ccdcb64.zip` | 12.8 MB | `05-应用软件/` | 轻量 CAN 分析软件（推荐） |
| `pcan-basic.zip` | 9.7 MB | `05-应用软件/cangaroo源代码/` | cangaroo 的 PEAK PCAN 插件 SDK |
| `cangaroo-master.zip` | 8.3 MB | `05-应用软件/cangaroo源代码/` | cangaroo 源码 |
| `ImpulseRC_Driver_Fixer.exe` | 5.8 MB | `04-烧录驱动及工具/` | DFU 驱动修复工具 |
| `zadig.zip` | 5.3 MB | `08-WIN7下使用说明/` | Win7 下装 USB 驱动 |

## 官方下载（建议优先）

这些工具都有官方最新版，Release 里的版本只是为了离线可用：

| 工具 | 官方地址 |
|---|---|
| cangaroo | <https://github.com/HubertD/cangaroo/releases> |
| TSMaster | <https://www.tosunai.com/> |
| BUSMASTER | <https://github.com/rbei-etas/busmaster> |
| cantact | <https://github.com/linklayer/cantact> |
| STM32CubeProgrammer | <https://www.st.com/en/development-tools/stm32cubeprog.html> |
| STM32 ST-LINK Utility | <https://www.st.com/en/development-tools/stsw-link004.html> |
| DfuSe / ST DFU | <https://www.st.com/en/development-tools/stsw-stm32080.html> |
| ARM GNU Toolchain | <https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads> |
| Zadig | <https://zadig.akeo.ie/> |
| ImpulseRC Driver Fixer | <https://impulserc.com/pages/downloads> |
| canable2-fw 源码 | <https://github.com/normaldotcom/canable2-fw> |

## 版权说明

Release 里的安装包版权归各自厂商（STMicroelectronics、同星智能、PEAK-System、Linklayer Labs 等）所有，
这里只是为了离线保存。正式项目请从官网下载最新版，并遵守对应的软件许可。
