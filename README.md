# mijia-cloud-control · 米家智能家居云 API 控制

**用一句自然语言控制全屋米家设备** —— 不依赖 Home Assistant、不刷固件，走小米云 API 直连。

## 这是什么

一套在 Hermes Agent 上实测跑通的米家控制方法论 + 脚本，覆盖：登录链路 → 设备清单 → 状态查询 → 开关/亮度/模式控制 → **音乐律动灯效**。

## 亮点

| 能力 | 说明 |
|---|---|
| 全链路实测 | 2026-08 打通：网页登录 + 短信验证码 + 已验证 deviceId（小米已封死 OAuth2 password grant） |
| 81 台设备清单化 | 按网段/网关归属分房，控制前先校验在线状态与归属，避免误操作 |
| 灯光能力分层 | 区分「瞬开瞬灭型」与「固件渐变型」，据此做音乐律动对位（强拍硬闪 + 弱拍呼吸） |
| 视频回分析法 | `scripts/analyze_light_video.py` 用录制视频逐帧测光，量化延迟/偏差，反推云端调用时序 |
| 一键口令方案 | 把「对小爱说一句话」变成助手可读的设备状态事件（绕开云端不能触发场景的限制） |

## 目录

```
SKILL.md                          # 方法论主体：登录/查询/控制/灯效设计
references/device-inventory.md    # 设备清单（已脱敏：型号 + 分组）
references/music-rhythm-lighting.md # 音乐律动灯效玩法（参数、限制、对位组合）
references/house-device-ownership.md # 多套房归属规则（只读/可操作边界）
references/home-assistant-migration-plan.md # 迁移 HA 的评估
scripts/rhythm_flash.py           # 律动闪灯
scripts/analyze_light_video.py    # 视频逐帧测光分析
```

## 快速开始

1. 用 `MijiaCloud` 类（见 SKILL.md「凭据与核心库」）登录取 token（30 天有效）
2. 拉设备清单 → 按分组确认目标设备
3. 控制前先查在线状态 → 串行下发（云端调用 110-180ms，禁止并发）

## 设计取舍

- **为什么不用 HA**：HA 的边缘网关更稳定，但需要额外硬件与维护；本方案零额外硬件、直接复用现有米家账号
- **为什么不并发**：云端对单账号并发敏感，串行调用避免限流与顺序错乱
- **为什么做时长对比**：均匀闪烁听感上「没有律动」——律动来自时长对比与多灯对位

## 备注

公开版本已脱敏：移除真实 DID、内网 IP、小区/WiFi 名称与账号信息。方法论与脚本可直接复用。
