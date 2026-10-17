# 09 - 常见问题（FAQ）

## 基础

### Q1. 这块板子到底是什么？

STM32G431CBT6 的 USB 转 CAN 适配器，CANable 2.0 兼容设计，Type-C 供电/通信，3Pin CAN 端子，板载 120Ω 终端电阻跳线，SWD 调试口，BOOT0 跳线。默认烧 slcan 固件。

### Q2. 支持 PCAN 吗？能用 PCAN-View 吗？

**不支持。** 本包没有 PCAN 固件，设备不会枚举成 PEAK 设备，PCAN-View / PCAN-Basic API 都认不到。
资料里的 `pcan-basic.zip` 只是给 cangaroo 上位机添加“连接正版 PEAK 硬件”的插件 SDK，不是给这块板子用的。
python-can 的 `bustype='pcan'` 也只适用于 PEAK 卡。

替代方案：cangaroo、TSMaster、BUSMASTER、python-can（slcan/socketcan）。

### Q3. 支持 CAN FD 吗？

- MCU 和 **slcan 固件支持**（数据段 2M/5M，beta）。
- **candleLight 固件不支持**。
- **收发器如果是 TJA1050，不能可靠跑 FD**；需要 TJA1051T-3 或同级 FD 收发器。
- 上位机要用支持 slcan FD 的，比如 cangaroo；python-can 的 slcan 后端不支持 FD。

详见 [08-canfd.md](08-canfd.md)。

### Q4. 两种固件怎么选？

- 默认/要 FD/要串口：**slcan**。
- Linux 原生 `can0`/高吞吐：**candleLight**（但只能经典 CAN）。
- 两个可以反复互刷。

## 连接与驱动

### Q5. 插上电脑没反应 / 设备管理器没有 COM 口

1. 换一根**能传数据**的 Type-C 线（很多线只能充电）。
2. 换 USB 口，避开 USB Hub。
3. Win10/11 应该免驱；Win7 需要装驱动（[07-win7.md](07-win7.md)）。
4. 看设备管理器有没有黄色感叹号；有的话卸载设备再拔插。
5. 板子是否在 DFU 模式（BOOT0 还短接着）？DFU 模式不会出 COM 口。

### Q6. 设备管理器显示 `DFU in FS Mode`

说明 BOOT0 还短接着，或者刚才快速拔插触发了 DFU。断开 BOOT0，拔插一次即可。
如果一直进 DFU，检查 BOOT0 跳线是否短路/按键卡住。

### Q7. 设备管理器显示 `STM Device in DFU Mode`

这是装了 ST 的 DfuSe 驱动。网页烧录工具只认 `DFU in FS Mode`，要先用 DfuSe Demo 烧，或在设备管理器卸载后重新短接 BOOT0 上电。

### Q8. 网页烧录后再也进不去 DFU / 认不到设备

1. 设备管理器卸载 `STM Device in DFU Mode`（勾选删除驱动）。
2. 断电，短接 BOOT0，再上电。
3. 确认出现 `DFU in FS Mode`。
4. 还不行就用 ST-LINK 通过 SWD 烧，最稳。

### Q9. COM 口被占用 / 打不开

cangaroo、串口助手、TSMaster 同时只能有一个打开同一个 COM 口。关掉其它程序；或拔插后重新选口。

### Q10. 为什么拔插要等 3 秒？

固件把“1 秒内快速重新上电”当作进入 DFU 的请求。正常使用时拔出后等 3 秒再插，避免误进 DFU；想升级时反过来，1 秒内插回。

## 总线与收发

### Q11. 能发不能收 / 一直报错

按顺序检查：

1. `CAN_H` / `CAN_L` 是否接反。
2. 是否共地（非隔离板必须共地）。
3. 终端电阻：总线两端各 120Ω；本板 P2 跳线是否投入。
4. 波特率是否和总线一致。
5. 总线上是否有第二个节点 ACK（只有一个节点时发送会失败/重试）。
6. 线太长、支线太长、干扰大。

### Q12. 终端电阻怎么设？

- 总线两端各 120Ω，中间节点不接。
- 台面上两个节点、线很短：两端都接，或只接一端试试。
- 断电用万用表测 `CAN_H`-`CAN_L`：约 60Ω 说明两个 120Ω 并联，正常；约 120Ω 说明只有一端；无穷大说明都没接。

### Q13. FD 帧发不出去 / 对方没反应

1. 收发器是不是 TJA1050？是的话换板/换收发器。
2. 固件是不是 slcan？candleLight 不行。
3. 上位机是否真的发了 FD + BRS？DLC 是否 ≥9？
4. 对方节点是否支持 FD，数据段波特率是否一致（2M/5M）？
5. 总线上有没有经典 CAN 节点？FD 帧会让经典节点报错。
6. 线材/终端是否适合 5M（尽量短）。

### Q14. 经典 CAN 能跑到多少？

slcan 支持 `S8` = 1 Mbit/s；再高就不是经典 CAN 了。实际能跑多少取决于线材、终端、节点。

### Q15. 5V 从哪来？CAN 端子能给别人供电吗？

本板 CAN 端子是 3Pin（CAN_H/CAN_L/GND），**没有 5V 输出**，不要按官方 CANable 的 4Pin 图去接。
板子由 Type-C 供电；CAN 侧不要额外灌 5V。

## 软件

### Q16. cangaroo 里 Bitrate 填什么？

填 **CAN 总线波特率**，例如 500000，不是串口波特率。串口参数对 USB CDC 没有意义。
FD 数据段填 `CanFD Bitrate`，2M 填 2000000，5M 填 5000000。

### Q17. DBC 文件怎么加载？

cangaroo 的 `Network1` 窗口 → `Can Databases` → 添加 `.dbc`。不需要解析就跳过。
TSMaster/BUSMASTER 也有各自的 DBC 加载入口。

### Q18. Python 报 `CanInitializationError`

- Windows：COM 口号对不对？是否被占用？
- Linux socketcan：`can0` 是否 `up`？
- 是否装在了另一个 Python 环境？用 `python3 -m pip install python-can`。
- slcan 的 channel 写 `COM4` 或 `/dev/ttyACM0`，不要写 `can0`。

### Q19. python-can 能发 FD 吗？

不能（slcan 后端）。要脚本化 FD，按 [08-canfd.md](08-canfd.md) 的串口协议用 `pyserial` 自己封装，或改用支持 FD 的第三方固件/工具。

### Q20. Linux 下没有 can0

- candleLight 固件才有原生 `can0`；slcan 固件要用 `slcand` 映射。
- 内核要开 `gs_usb`（candleLight）或 `slcan`。
- `dmesg | tail` 看 USB 枚举情况。

## 烧录与恢复

### Q21. 用 ST-LINK 烧录地址填多少？

`.bin` 填 **`0x08000000`**。

### Q22. 烧完不启动

- BOOT0 是否还短接？断开再上电。
- 是不是烧了错误的固件（candlelight 烧成 slcan 的地址？两者都在 0x08000000，一般没事）。
- 用 CubeProgrammer 全片擦除后重烧。
- 检查 3.3V 和 SWD 接线。

### Q23. 板子变砖了

ST-LINK + CubeProgrammer，`Connect under reset`，全片擦除，烧 `0x08000000`。STM32 的系统 Bootloader 在独立区域，正常擦不掉，所以基本都能救。

### Q24. 能不能用 USB DFU 烧 `.bin`？

DFU 工具要 `.dfu` 文件（DfuSe/网页）；ST-LINK/CubeProgrammer 用 `.bin`。两种文件本包都提供了。

## 机器人关节电机项目相关

### Q25. 用来调试关节电机需要注意什么？

- 电机驱动器/强电和 CAN 分析仪共地会引入干扰，必要时用隔离 CAN 收发器或隔离 USB。
- 总线两端 120Ω，电机节点多时不要每个都接终端。
- 先低速（125k/250k/500k）验证协议，再上 1M。
- 抓包时开时间戳，方便对齐控制周期。
- 需要 FD 时确认驱动器和收发器都支持相同数据段波特率。
- 长时间录制建议用 TSMaster/cangaroo 的日志功能，不要只靠串口助手。
