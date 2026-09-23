# 米家设备清单（81台）· 两套房归属

> 2026-08-19 全量拉取。分类依据：localip 网段 + ssid + parent_id 网关映射。

## <小区名>（A房 · 192.168.31.x · 默认控制目标）

### WiFi 直连 26台
| 设备 | model | IP |
|------|-------|----|
| 客厅灯 | lemesh.light.wy02 | <LAN_IP> |
| 书房灯 | lemesh.light.wy02 | <LAN_IP> |
| 卧室灯 | lemesh.light.wy02 | <LAN_IP> |
| 次卧灯 | lemesh.light.wy02 | <LAN_IP> |
| 餐厅灯 | yeelink.light.ceil45 | <LAN_IP> |
| 卧室台灯 | yeelink.light.lamp1 | <LAN_IP> |
| 台灯 | philips.light.sread9 | <LAN_IP> |
| 卧室浴霸 | xiaomi.bhf_light.s1 | <LAN_IP> |
| 客卫浴霸 | xiaomi.bhf_light.na1 | <LAN_IP> |
| 厨宝 | zimi.waterheater.h03 | <LAN_IP> |
| 油烟机 | cykj.hood.jyj22 | <LAN_IP> |
| 电磁炉 | chunmi.ihcooker.chefnic | <LAN_IP> |
| 电饭煲 | chunmi.cooker.normal2 | <LAN_IP>（离线） |
| 空气炸锅 | careli.fryer.maf04 | <LAN_IP> |
| 晾衣架 | xiaomi.airer.pro3 | <LAN_IP> |
| 摄像头 | chuangmi.camera.061a01 | <LAN_IP> |
| 屏幕 | chuangmi.plug.m1 | <LAN_IP> |
| 马桶 | chuangmi.plug.212a01 | <LAN_IP> |
| 电视机 | xiaomi.tvbox.b1 | <LAN_IP>（离线） |
| 电扇 | dmaker.fan.p5 | <LAN_IP> |
| 小爱音箱 Ultra | xiaomi.wifispeaker.oh2p | <LAN_IP> |
| 小爱音箱 pro | xiaomi.wifispeaker.lx06 | <LAN_IP> |
| 小爱音箱Play | xiaomi.wifispeaker.l05c | <LAN_IP> |
| 米家网关 | lumi.gateway.v3 | <LAN_IP>（did=<DID>） |
| 路由器 | xiaomi.router.rd15 | <LAN_IP> |
| 网管 | xiaomi.router.rd08 | <LAN_IP> |

### 网关子设备 7台（parent_id=<DID>，ssid=IoT）
客卫传感器(lumi.sensor_motion.v2)、茶几小开关、书桌小开关、餐桌小开关、卧室床头小开关(lumi.sensor_switch.v2)、阳台电蚊香液(lumi.plug.v1)、书桌电表(lumi.plug.v1)

## B房（B房 · 192.168.0.x · 禁操作）

### WiFi 直连 10台
| 设备 | model | IP |
|------|-------|----|
| 主卧空调 | zhimi.aircondition.ma4 | <LAN_IP> |
| 客厅空调 | zhimi.aircondition.ma4 | <LAN_IP> |
| 次卧空调 | xiaomi.airc.h10h00 | <LAN_IP> |
| Yeelight智能浴霸 | yeelink.bhf_light.v2 | <LAN_IP> |
| 洗衣机 | minij.washer.v8 | <LAN_IP>（离线） |
| 电扇 | dmaker.fan.p5 | <LAN_IP> |
| 米家电热毯 | xiaomi.blanket.mj1 | <LAN_IP>（离线） |
| 阳台灯 | chuangmi.plug.m1 | <LAN_IP> |
| 触屏音箱 | xiaomi.wifispeaker.lx04 | <LAN_IP> |
| 网关 | lumi.acpartner.v3 | <LAN_IP>（did=<DID>） |

### 网关子设备 7台（parent_id=<DID>，ssid=<SSID_B>）
主卧灯、厕所灯、客厅灯、走廊灯(lumi.ctrl_neutral2.v1)、主卧床头小开关、阳台小开关(lumi.sensor_switch.v2)、阳台门开关(lumi.sensor_magnet.v2，离线)

## 无 parent 蓝牙mesh 31台（推断属<小区名>，待用户确认）

| 类别 | 数量 | 设备 |
|------|------|------|
| 领普开关 linp.switch | 14 | 卧室灯、客卫灯、走廊灯、厨房灯、次卧灯×2、阳台灯、餐厅灯、卫生间灯、凉霸、衣帽间灯(t2dbw2)、走廊+阳台灯(t2dbw2)、一键关勿动、三键(t2dbw3) |
| mesh空调 lemesh.airc.air02 | 5 | 餐厅/客厅/次卧/卧室/书房空调 |
| 窗帘 lonsam.curtain.ct05 | 4 | 卧室布帘、客厅纱帘、客厅布帘、卧室纱帘 |
| 其他 | 8 | 门锁(loock.lock.v5)、水浸传感器、领普传感器ES5、温度计×2(miaomiaoce)、体重秤、充电器、小米手环 |

## 分类技术要点

1. `localip` 为空或公网IP（111.183.83.x/171.83.41.x/58.48.206.x）= 网关子设备/蓝牙mesh，不能靠网段分
2. `parent_id` 是最可靠的归属信号（网关 did 直接映射房间）
3. `ssid` 兜底：信号满满=<小区名>、<SSID_B>=B房、IoT=<小区名>（米家网关子设备）
4. `family_id` 全部为 0，无区分度
5. 快速分组脚本：`/opt/data/group_devices.py`（`/opt/data/mijia_venv/bin/python3` 运行）
