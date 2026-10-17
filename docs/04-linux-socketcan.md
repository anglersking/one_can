# 04 - Linux / 嵌入式 SocketCAN

两种固件在 Linux 下都能用，但方式不同：

| 固件 | 设备 | 映射方式 | CAN FD |
|---|---|---|---|
| **candleLight** | `/dev/ttyACMx` 不出现，直接是 `can0` | 内核 `gs_usb` 驱动，原生 SocketCAN | ❌ |
| **slcan** | `/dev/ttyACMx` | `slcand` 用户态程序映射成 `can0` | 经典 CAN；FD 需专用上位机 |

先装工具：

```bash
sudo apt update
sudo apt install can-utils
```

## 1. candleLight 固件（推荐）

插上板子后：

```bash
dmesg | tail
ip link
```

应该能看到 `can0`。启动并设置 500 kbit/s：

```bash
sudo ip link set can0 up type can bitrate 500000
```

老系统/老内核也可以：

```bash
sudo ip link set can0 type can bitrate 500000
sudo ifconfig can0 up
sudo ifconfig can0 txqueuelen 1000
```

收发测试：

```bash
candump can0
cansend can0 123#1122334455667788
```

常用工具：

```bash
canbusload can0@500000          # 总线负载
cansniffer can0                 # 滚动显示报文
cangen can0 -D 11223344DEADBEEF -L 8   # 周期发送
```

关闭：

```bash
sudo ip link set can0 down
```

> candleLight 的 CAN FD：本包里的 `ba6b1dd` 版本不支持 FD，`ip link` 里也不要加 `dbitrate`/`fd on`。
> 需要 FD 请用 slcan 固件 + cangaroo，或自行换支持 G431 的第三方 candlelight 固件。

## 2. slcan 固件

插上后出现 `/dev/ttyACM0`（编号可能是 0/1/2…）：

```bash
ls /dev/ttyACM*
```

映射成 can0 并设置 500 kbit/s：

```bash
sudo slcand -o -c -s6 /dev/ttyACM0 can0
sudo ifconfig can0 up
sudo ifconfig can0 txqueuelen 1000
```

`-s` 参数对应波特率：

| 参数 | 波特率 |
|---|---|
| `-s0` | 10 k |
| `-s1` | 20 k |
| `-s2` | 50 k |
| `-s3` | 100 k |
| `-s4` | 125 k |
| `-s5` | 250 k |
| `-s6` | 500 k |
| `-s7` | 750 k |
| `-s8` | 1 M |

之后同样用 `cansend` / `candump`。

> `slcand` 只实现了经典 CAN 的 slcan 协议，**不支持本固件的 FD 扩展命令**。
> 想在 Linux 上测 FD，只能用 cangaroo（有 Linux 版）或自己按 [08-canfd.md](08-canfd.md) 的协议写脚本。

## 3. 嵌入式 Linux（RK356x 等）

内核需要打开：

```text
[*] Networking support  --->
    <*> CAN bus subsystem support  --->
        CAN Device Drivers  --->
            CAN USB interfaces  --->
                <*> Serial / USB serial CAN Adaptors (slcan)
```

candleLight 还需要 `gs_usb`：

```text
CAN USB interfaces  --->
    <*> Geschwister Schneider UG and candleLight compatible interfaces
```

烧 slcan 固件时，内核日志会出现：

```text
usb 3-1: New USB device found, idVendor=1d50, idProduct=606f
cdc_acm 3-1:1.0: ttyACM0: USB ACM device
```

然后按上面的 `slcand` 步骤操作。嵌入式系统如果没装 `can-utils`，需要交叉编译后拷进去。

## 4. 权限与 udev

普通用户访问 `/dev/ttyACM0` 可能需要加入 `dialout`：

```bash
sudo usermod -aG dialout $USER
```

candleLight 建议加 udev 规则（上游仓库的 `70-candle-usb.rules`），避免每次 `sudo`。

## 5. 开机自动配置（可选）

`/etc/systemd/network/80-can.network`：

```ini
[Match]
Name=can0

[CAN]
BitRate=500K
```

或者用 `systemd-networkd`/`network-manager` 的 CAN 配置。机器人控制器上建议固定接口名，避免多设备时 `can0/can1` 顺序变化。

## 6. 常见问题

- `ip link` 没有 `can0`：candleLight 固件没烧对，或内核没开 `gs_usb`。
- `slcand: command not found`：`sudo apt install can-utils`。
- `RTNETLINK answers: Operation not permitted`：加 `sudo`。
- 能发不能收：终端电阻、接线、另一个节点是否 ACK。
- 总线错误 `BUS-OFF`：波特率不匹配或接线错误，`ip -details link show can0` 查看状态。
