# 02 - Windows 快速上手（slcan 固件 + cangaroo）

出厂默认固件是 **slcan**。在 Windows 10/11 上不需要装驱动，插上就是一个串口。

## 1. 接板子

1. 用 **能传数据** 的 Type-C 线连接板子和电脑。
2. 打开 `设备管理器 → 端口 (COM 和 LPT)`。
3. 应该看到类似：

   ```text
   USB 串行设备 (COM4)
   ```

   记下 COM 号。看不到就换线/换 USB 口，或看 [09-faq.md](09-faq.md)。

> 如果显示的是 `USB Serial Device`、`CDC` 之类也正常，只要在“端口”下面有 COM 号即可。
> 如果出现在“其他设备”并带黄色感叹号，说明系统没装上 CDC 驱动（Win7 常见，见 [07-win7.md](07-win7.md)）。

## 2. 安装 cangaroo

资料包里自带 `cangaroo-win32-ccdcb64.zip`，也可以从官方仓库下载最新版：

- <https://github.com/HubertD/cangaroo/releases>

解压后直接运行 `cangaroo.exe`（32 位程序，64 位 Windows 可以跑），无需安装。

> cangaroo 是开源软件；资料包里的版本较老。若发现不支持 CAN FD，换最新 release。

## 3. 建立连接

1. 菜单 `Measurement → Start Measurement`（或点工具栏的播放按钮）。
2. 弹出 `Network1` 窗口：
   - **Interfaces**：选中板子的 COM 口，例如 `COM4`；
   - **Bitrate**：`500000`（仲裁段波特率，按你的总线设）；
   - **CanFD Bitrate**：`2000000`（默认 2M，可改 5M；只跑经典 CAN 时无所谓）；
   - **Can Databases**：需要 DBC 解析就点 `+` 加载 `.dbc`，不需要就跳过；
   - **Listen Only**：只监听不回 ACK 时勾选（总线上只有这一个节点时不要勾）。
3. 点 `OK`。
4. 主界面出现总线报文即连接成功。

> cangaroo 里的 `Bitrate` 是 **CAN 总线波特率**，不是串口波特率。USB CDC 的串口参数对 slcan 固件没有意义。

## 4. 发送报文

1. 在 `Transmit` 面板新建一条消息。
2. 填 `ID`（标准帧 11 位 / 扩展帧 29 位）。
3. 选 `DLC`（数据长度）；FD 帧 DLC 可以到 15（对应 64 字节）。
4. 填数据，点 `Send`。

周期发送用 `Cyclic`/`Period` 设置。

## 5. 串口助手快速自检（可选）

不想装 cangaroo 时，可以用任意串口助手（波特率随便，115200 即可，8N1）打开 COM 口：

| 发送 | 预期返回 | 说明 |
|---|---|---|
| `V\r` | `b158aa7 github.com/normaldotcom/canable2.git` | 固件版本 |
| `E\r` | `CANable Error Register: 0` | 错误寄存器 |
| `S6\r` | 无返回（本固件不做 ACK） | 设 500 kbit/s |
| `O\r` | 无返回 | 打开通道 |
| `C\r` | 无返回 | 关闭通道 |

> 注意：这个 slcan 固件 **不返回 ACK/NACK**，只有 `V`、`E` 和收到的 CAN 帧会回数据。
> 发送帧用 `t/T/r/R`（经典）和 `d/D/b/B`（FD），格式见 [08-canfd.md](08-canfd.md)。

## 6. 需要 CAN FD 时

必须同时满足：

1. 板上收发器是 **TJA1051T-3** 或同级 FD 收发器（TJA1050 不行）；
2. 固件是 **slcan**（candleLight 不支持 FD）；
3. 上位机支持 slcan FD（cangaroo）；
4. 总线上其他节点也支持相同的数据段波特率（2M 或 5M）。

cangaroo 里设置：

```text
Bitrate:       500000     # 仲裁段
CanFD Bitrate: 2000000    # 数据段，可改 5000000
```

发送时选 FD 帧 + BRS，DLC 按实际长度选（9=12 字节 … F=64 字节）。

详见 [08-canfd.md](08-canfd.md)。

## 7. 其他 Windows 上位机

| 软件 | 支持固件 | 说明 |
|---|---|---|
| **cangaroo** | slcan（含 FD）/ candleLight | 推荐，轻量、开源 |
| **TSMaster** | candleLight | 功能强，带 DBC、仿真、录制；资料包说明只写了 candleLight |
| **BUSMASTER** | candleLight | 老牌开源工具 |
| **cantact** | candleLight | Java 程序，需 JRE |
| 串口助手 / 自写脚本 | slcan | 只能手工发命令，适合验证 |

> 这些工具体积较大或有版权，仓库没有上传，按 README 的链接下载。

## 8. 常见问题

- **COM 口打不开**：被串口助手/TSMaster 占用了，先关掉其他程序。
- **能发不能收**：终端电阻、CAN_H/L 接反、总线上没有其他节点 ACK。
- **一收就报错**：波特率不匹配；或对方是 FD 而你在经典 CAN 模式。
- **设备管理器里有两个 COM 口**：正常，CDC 有时会多枚举一个调试口；以能收到 `V` 回复的为准。
