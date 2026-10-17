# 06 - 从源码编译固件

本包只提供 **slcan 固件** 的源码，candleLight 只有编译好的 bin/dfu。

## 1. 源码位置

原始资料：`canable2-fw.tar.bz2`（31 MB，带 `.git`），放在 GitHub Releases：

> <https://github.com/anglersking/one_can/releases/tag/v1.0-resources>

上游仓库：<https://github.com/normaldotcom/canable2-fw>，本包对应 commit **`b158aa7`**。

```bash
tar xvf canable2-fw.tar.bz2
cd canable2-fw
git log --oneline -3
```

关键文件：

```text
src/can.c          FDCAN1 初始化、收发
src/slcan.c        slcan 命令解析/组帧
src/main.c         主循环
src/usbd_*         USB CDC
Makefile           构建脚本（输出 canable2-<git版本>.bin/.hex）
```

## 2. 工具链

资料包自带的编译器在 Releases（`gcc-arm-none-eabi-5_4-2016q2-20160622-linux.tar.bz2`），也可以装系统包：

> <https://github.com/anglersking/one_can/releases/tag/v1.0-resources>

```bash
tar xjf gcc-arm-none-eabi-5_4-2016q2-20160622-linux.tar.bz2
export PATH=$PWD/gcc-arm-none-eabi-5_4-2016q2/bin:$PATH
arm-none-eabi-gcc --version
```

也可以装系统包：

```bash
sudo apt install gcc-arm-none-eabi
```

> 新版 GCC 可能报 warning，但不影响生成固件。

## 3. CMake

要求 **CMake ≥ 3.13**：

```bash
cmake --version
```

不够的话，资料包 `linux下cmake安装.txt` 给了从源码装 3.16 的步骤：

```bash
sudo apt remove cmake
cd /usr/src
wget https://github.com/Kitware/CMake/releases/download/v3.16.0/cmake-3.16.0.tar.gz
tar -zxvf cmake-3.16.0.tar.gz
cd cmake-3.16.0
sudo apt install libssl-dev build-essential
./bootstrap && make -j$(nproc) && sudo make install
```

## 4. 编译

```bash
cd canable2-fw
make
```

产物在 `build/`：

```text
build/canable2-b158aa7.bin
build/canable2-b158aa7.hex
```

如果 git 版本号带 `-dirty`，说明工作区有未提交改动，正常。

## 5. 烧录

```bash
# 方式 1：dfu-util（需要板子已在 DFU 模式，BOOT0 短接上电）
make flash

# 方式 2：ST-LINK
STM32_Programmer_CLI -c port=SWD -w build/canable2-b158aa7.bin 0x08000000 -v -rst
```

## 6. 改波特率/采样点/终端电阻

- 波特率由 slcan 命令 `S0`–`S9` 在运行时设置，不需要改源码。
- FD 数据段由 `Y2`/`Y5` 设置。
- 终端电阻是硬件跳线 P2，与固件无关。
- 采样点、时钟分频在 `src/can.c` 的 `FDCAN_Init` 里，改之前先确认晶振配置（默认使用内部时钟，`INTERNAL_OSCILLATOR`）。

## 7. candleLight 源码

本包没有附 candleLight 源码。上游对应分支：

- <https://github.com/normaldotcom/candleLight_fw/tree/multitarget>

注意：上游 candleLight_fw 主线**不支持 STM32G431**，本包的 `ba6b1dd` 是 canable 的定制构建，只有 bin/dfu。想要能跑 FD 的 candlelight，需要找支持 G431 的第三方固件（例如 Elmue 的 CANable 2.5），不属于本资料包内容。

## 8. Windows 编译

不推荐。原说明也写了“Windows 上编译（不建议使用）”，需要 Qt、MinGW、ARM 工具链，问题较多。建议在 Linux/WSL 里编译，或者直接用现成固件。
