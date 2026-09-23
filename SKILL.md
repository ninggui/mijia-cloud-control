---
name: mijia-cloud-control
description: 米家智能家居云API控制（2026实测）。触发：控制米家设备、查设备状态、智能家居、开灯关灯、调空调窗帘。
---

# 米家智能家居云 API 控制

> 2026-08-19 全链路实测打通：登录→设备列表(81台)→状态查询→开关控制。小米已封死 OAuth2 password grant，必须走网页登录+短信验证码+已验证 deviceId。

## 凭据与核心库（已就位）

| 资产 | 路径 |
|------|------|
| 登录凭据 | `/opt/data/mijia_token_cache/full_auth.json`（ssecurity/serviceToken/userId，**30天有效**） |
| 控制库 | `/opt/data/skills/@clawhub_lanlan314/xiaomi-miot-lan/mijia_api.py`（MijiaCloud 类） |
| 完整登录脚本 | `/opt/data/full_login.py`（凭据过期时重跑） |
| 设备清单 | `/opt/data/mijia_token_cache/devices_result.json`（81台，含 did/model/在线状态） |
| Python 环境 | `/opt/data/mijia_venv/bin/python`（含 requests + python-miio/micloud） |

## 常用操作

```python
import sys; sys.path.insert(0, "/opt/data/skills/@clawhub_lanlan314/xiaomi-miot-lan")
from mijia_api import MijiaCloud
mc = MijiaCloud()
devs = mc.device_list()                    # 全部设备
r = mc.miio_rpc(did, "get_prop", ["power"])   # 查开关状态 → result: ['on'/'off']
r = mc.miio_rpc(did, "set_power", ["on"])     # 开
r = mc.miio_rpc(did, "set_power", ["off"])    # 关
```

- did 从 device_list 或 devices_result.json 取（如阳台灯插座 did=<DID>）
- 响应 `{"code":0,"message":"ok","result":[...]}` 即成功
- **灯具类（lemesh/yeelink 等 MIoT 设备）miIO rpc 报 `undefined command`，必须走 MIoT spec 端点**（2026-09-05 实测）：
  - 查属性：`mc.api('/miotspec/prop/get', {'params': [{'did': DID, 'siid': 2, 'piid': 1}]})`
  - 设属性：`mc.api('/miotspec/prop/set', {'params': [{'did': DID, 'siid': 2, 'piid': 1, 'value': True}]})`（灯电源 siid=2, piid=1, True=开 False=关）
  - 传统插座（chuangmi.plug.*）才走 miio_rpc set_power
  - **非标准 siid**：晾衣架灯 airer.pro3 的灯服务在 siid=3（piid1=电源 / piid2=亮度），siid=2 无效——控制前先 prop/get 遍历 siid 1-10 探有效 code=0 的属性，别假设灯具都在 siid=2
- **测试/演示纪律**：动设备前先读原状态，结束后恢复（尤其调光亮度、开关）——用户在家时突兀的灯状态变化会被注意到；演示脚本一律 try/finally 兜底关灯

## 凭据快速刷新（优先用这个，不用短信）

401 auth error = serviceToken 失效。passToken 长期有效（直到改密码），直接重登：`/opt/data/mijia_venv/bin/python /opt/data/full_login.py` → 自动换新 ssecurity/serviceToken 并保存。full_login.py 依赖 browser cookie（`/opt/data/cache/browser-use/workspace/20260818_220718_560348e9/mijia_all_tokens.json`）。实测 passToken 跨月仍有效，重登无需短信验证码。

**过期症状是「静默空列表」，不是报错**（先看这两条再决定要不要重登）：
- `mc.device_list()` 返回 `[]`（不抛异常）+ 任意 `mc.api(path, {})` 返回 `{"http":401,"raw":"{\"code\":3,\"message\":\"auth error\"}"}` → serviceToken 失效。**不要误判成"账号不对/设备没了/接口下线"**，直接重登即恢复
- `MijiaCloud.api(path, payload)` 第二个参数必传（签名 `api(self, path, payload, method="POST")`）——只传 path 报 `missing 1 required positional argument: 'payload'`；探测未知接口传 `{}` 即可

## 视频实测：渐变对"看起来闪不闪"的影响（2026-09-22，用户手机录像 + 逐帧分析）

分析方法（不依赖 PIL/numpy）：`/opt/data/scripts/analyze_light_video.py` + 自建"饱和像素占比"指标（每帧 >=235 的像素比例）——比区域均值干净得多，手机自动曝光会污染均值曲线。

实测结论（客厅灯 lemesh <DID>）：
- **上升快、下降慢**：亮起约 0.2s；熄灭带约 0.75-0.8s 渐变尾巴（设渐变 1 秒时）
- **渐变模式下快切 = 看起来常亮**：每 1 秒切换时，饱和度指标连续 9.45 秒不掉（肉眼就是一直亮）；每 2 秒切换也只剩 0.3 秒的暗窗口 → **要跟拍必须用「立即模式」（siid4 p3=1）**
- 立即模式下亮灭都干脆（0.05-0.1s 级），录像里能拍到干净的明灭
- 手机录像分析铁律：用"饱和像素占比"而不是区域平均亮度；灯区域选"摆幅大 + 双峰性高"的格子
- **手持录像分不清哪盏是哪盏**：抖动 + 自动曝光下只有"最大的饱和亮区"能可靠分离（其余灯达不到饱和，混在噪声里）→ **不要靠视频给多盏灯认位**。要确认"设备 ↔ 看到的灯"对应关系，跑 `scripts/light_id_test.py`：一次只亮一盏、按 客厅→阳台→造型 顺序各闪 2 次（约 10 秒），让用户肉眼看顺序确认。这也比视频识别更可靠、更快
- 录像要有效就要求用户**固定机位**；手持录像只用于看"渐变/常亮"这类整体亮度趋势，不用来定位

## 音乐↔灯光 同频标定（2026-09-22 实测定稿）

**启用约定（用户明确）**：灯光秀/待命监听**不常驻**——只在用户主动说"挂监听/开始"时才启动；用完即停，不后台长跑（省额度）。2026-09-22 玩完一次后已全部停掉。

脚本 `/opt/data/scripts/calibrate_sync.py`：喂一段"带声音的视频"（画面有灯 + 能听到音乐），输出三个硬数字：
| 指标 | 判据 | 实测样例 |
|---|---|---|
| 灯第一次亮 | 画面亮度**去趋势**（减 0.5s 滑动均值）≥0.35×max，合并 0.15s 内重复 | 8.83s |
| 音乐出现 | 低频（<200Hz）包络的**节奏分**（4s 窗、0.3-0.6s 滞后自相关）≥0.40 且低频均值 ≥0.05，持续 ≥3s | 11.0s |
| 首拍 | 低频明显鼓点首次出现（0.35s 合并双峰后的峰） | 14.1s |

**坑（都踩过）**：
- 别用"整体音量"找音乐起点 —— 用户人声/小爱应答会把低频推高，误报 0.3s。必须用**节奏分 + 持续 3 秒**双条件（人声窗节奏分 0.2-0.38，音乐窗 0.45-0.65）。
- 别用"饱和像素"找灯 —— 手机自动曝光会压亮度。用去趋势后的亮度。
- 手机录音测 BPM 只能当参考（同一段测出过 92/120/150）——**BPM 以源文件为准**，视频只用来测"灯 vs 音乐"的时间差。

实测结论（《APT.》+ 三灯，2026-09-22）：灯比音乐早 **2.2s**（相对音乐起）/ **5.3s**（相对第一声鼓点）。根因：小爱音箱从收到命令到出声要 **5-7 秒**（搜索+缓冲），固定 `--show-delay` 只能覆盖平均值。

**标定闭环（同日二次验证）**：把 `--show-delay` 2.5 → **5.0 秒** + 轮询 2s → 1s 后，同一流程重测：灯 11.07s / 音乐 11.00s → **差 +0.07 秒**（已对齐）。结论：`SHOW_DELAY = 5.0` 是当前音箱的正确补偿值；换歌/换时段需重测（音箱启动延迟浮动 5-7s）。

### 编舞 v3（丢事件从 44% 降到 7%）
同一盏灯的相邻两条指令必须 **≥0.25s**，否则来不及（云端往返 110-350ms）—— v2 用 8 分音符（0.2s）导致 `完成 359/640 | 丢弃 281`。v3 改为：客厅灯每 2 拍闪（亮 1 拍）、阳台灯第 1/3 拍、造型灯第 2/4 拍，左右交替。

### 待命脚本启动保护
`light_show_watcher.py` 启动时若信号灯已是『开』→ **只复位、不开演**（早期版本会立刻跑一场，用户会被吓到）。

## 客厅灯渐变参数（2026-09-21 实测，用户提醒后找到）

现象：远端连续开关该灯，肉眼看到的是"一直常开/常闭"——因为**默认渐变时长 30 秒**，快闪根本走不完渐变。

lemesh.light.wy02（did <DID>）相关属性：
- **siid4 piid3**：0=Gradient 渐变（默认）/ **1=Immediately 立即**（可写，实测回读一致）
- **siid2 piid10 / piid11**：渐变时长（1-60 秒，实测默认 **30**）
- siid2 piid12 / piid13：渐变终点/起点亮度（默认 80）
- siid2 piid5：模式（0=WY，4=Day，5=Night，7=Warmth…19=Mode4）；siid2 piid7：上电默认态；siid2 piid8/9：助眠/唤醒

用法：**演出前把 siid4 piid3 设为 1（立即）或把 p10/p11 设为 1 秒 → 演出后原值恢复**（light_show.py 的 `--gradient immediate|short|keep` 已内置）。
注意：`siid2 piid2` 亮度是目标值，渐变过程中不会变（拔不了渐变曲线，只能靠肉眼判断）。

## 灯光秀脚本 light_show.py（2026-09-21 用户选定三灯组合，已实测）

- 脚本家族（均在 `/opt/data/scripts/`，用 `/opt/data/mijia_venv/bin/python` 跑）：`light_show.py`（通用律动，预设 pop/waltz/build，`--bpm/--bars/--delay/--gradient/--dry`）、`light_show_apt.py`（《APT.》专用编舞 v3：客厅灯每 2 拍闪、双瞬灯整拍左右交替——**同一盏灯相邻指令必须 ≥0.25s**，8 分音符方案实测丢 44% 事件）、`calibrate_sync.py`（从带声视频标定"灯 vs 音乐"时间差）、`light_show_watcher.py`（待命监听触发插座）、`light_show_stop.py`（立即停止 + 按快照恢复 + 回读复核）、`detect_bpm.py`（从录音/带声视频测真实 BPM 与首拍时刻）、`light_id_test.py`（一盏一盏点名）、`light_ramp_visual_test.py`（四段观感校准）、`analyze_light_video.py`（录像亮度分析）
- 用户选定组合（同一区域、瞬缓对位）：**客厅灯 lemesh <DID>（缓）+ 阳台灯 linp <DID>（瞬）+ 造型灯=领普三键 <DID> siid4 piid1（瞬）**
- **实测延迟（2026-09-21）**：客厅灯 353ms / 阳台灯 107ms / 造型灯 124ms；阳台灯 200ms 间隔连闪 6/6 成功 → 8 分音符可行；客厅灯亮度 0→100 往返 727ms（渐变，只适合整拍）
- **串行调度必漂移（踩坑）**：按时间轴串行 `sleep`+调用，160 事件实测平均偏差 2.5s（每个调用阻塞 100-350ms 累积）→ 修复：**每盏灯一个工作线程**（各自 queue + 迟到 >300ms 事件丢弃），调度线程只投递时间戳
- **延迟补偿**：发指令时间 = 拍点 − 该灯实测延迟（LAT 表），让"灯亮"落在拍点上；补偿后 160 事件最大偏差 101ms
- 播放脚本必须 try/finally 恢复原状态；结束打印 事件数/平均偏差/最大偏差/丢弃数
- 小爱音箱型号（家庭实测清单）：**Ultra = xiaomi.wifispeaker.oh2p（did <DID>，客厅）**、小爱音箱 pro = lx06、小爱音箱Play = l05c、触屏音箱 lx04（离线）
- **凭据 30 天会过期**（09-05 刷新、09-21 实测 401）→ 重跑 `/opt/data/mijia_venv/bin/python /opt/data/full_login.py` 免短信直接续（passToken 长期有效）

## 灯效观感实测与验证（动真灯前必读）

- **点灯测试先等用户口令，然后倒计时 5 秒再起跑**（用户要站到能同时看到多盏灯的位置）；脚本一律 try/finally 恢复原状态，跑完回读复核并报告复核结果
- 四段观感校准脚本：`/opt/data/scripts/light_ramp_visual_test.py --delay 5`（A 渐变1秒·2秒周期×3 → B 渐变1秒·1秒周期×4 → C 立即模式·0.5秒快闪×8 → D 三灯合体 4 小节），约 28 秒。用户反馈"哪段开始发虚"即得出该灯能跟拍的最小周期——**别用参数表推算，用眼睛测**
- **云端读不到实际明灭**：`siid2 piid2` 是目标值，渐变过程中不变；摄像头（chuangmi.camera.061a01）拿不到流，容器也到不了内网 → 让用户手机**固定机位**录一段（画面含目标灯、每段之间停 1-2 秒），再用 `scripts/analyze_light_video.py`（本 skill，纯 stdlib+ffmpeg）算亮度曲线，得出实际渐变时长与"到全灭"的时刻
- 已定参数：口令「**开始表演**」；**客厅灯演出时必须用「立即模式」（`--gradient immediate`）**——录像逐帧实测：渐变 1 秒下每 1 秒切换会连续 9.45 秒看起来常亮、每 2 秒切换也只剩 0.3 秒暗窗口，根本跟不了拍；渐变只适合 ≥4 秒周期的慢呼吸；触发插座=阳台电蚊香液（用户已同意借用）

## 灯光节奏/律动控制（2026-09-05 实测）

- 灯具律动走 `/miotspec/prop/set`（同开关），云端单次调用延迟实测 110-180ms → 拍子 ≥0.5s 才稳，BPM 80-140 区间效果好
- **律动感 = 时长对比，不是均匀开关**（用户纠偏：等间隔闪烁"仅仅是连续开关开关，没有律动"）：短音/长音/乐句停顿必须拉开（如 0.66s / 1.32s / 句间 1.2s），旋律线条才"看得见"
- 可复用模板：`scripts/rhythm_flash.py`（小星星 4 句，改 DID/时值/旋律序列即换歌换灯）
- **两灯交替对位律动**（用户思路）：瞬闪灯（领普开关/插座控）做"咔"强拍 + 渐变灯（lemesh/yeelink/晾衣架）做"呼"弱拍，或双瞬闪灯 8 分音符左右交替——比单灯闪律动感强一个量级；设备瞬/缓分类与玩法参数见 `references/music-rhythm-lighting.md`
- 播放脚本必须 try/finally 兜底关灯，防中途异常灯常亮
- 串行执行，禁止并发（多灯同步也是循环串行调）

## 小爱音箱云端音频通道（2026-09-05 实测）

- **云端 API 无免确认音频通道**：set_text / speak / intent / v2/tts/speaker / miotspec/action 全部 `user ack timeout`（exe_time≈4s = 等音箱端真人确认超时）——小米封了免确认 TTS/播歌
- 别在音箱上轮番试 TTS 变体：每次白白等 4s 超时，且响应无区分度
- 替代路径：用户语音触发（"小爱同学播放X"）→ 听到音乐启动灯闪（云端 ~0.15s 延迟可跟上节奏）；精确毫秒级联动需中枢本地化/HA

## 自动化/场景接口（两次复核均确认：拿不到）

- `/scene/list`、`/v2/scene/list` 返回 `{"code":0,"message":"ok","result":{}}`（空对象，需 home_id）；`/automation/list` 及 v2/v3 变体、`/home/home_list`、`/v2/home/home_list`、`/home/room_list`、`/scene/manual/list` **全部 404** → 拿不到 home_id，也列不出/触发不了米家手动场景
- **结论：米家未开放自动化/场景管理 API，自动化本地化切换只能米家 App 手动**（智能→自动化→编辑→右上角菜单→本地化执行）；米家 Web（home.mi.com / iot.home.mi.com）也没有智能管理功能
- 直接推论：**任何"一个口令同时触发小爱播歌 + 灯效"的自动化，都不可能由云端 API 发起**（播歌本身也被封，见上节）——只能靠 ① 小爱本地语音/训练 ② HA 本地化。三条触发路径的能力对比与推荐见 `references/music-rhythm-lighting.md` 末节「一句话触发的三条路径」

## 一句话触发的落地模式（触发设备当事件源，已端到端跑通）

云端不能建场景，但可以**把一个可读写的米家设备当"事件信号"**，把用户在 App 里配的口令变成助手能轮询到的状态变化：

1. 用户在 App 配一次：口令「**开始表演**」→ 动作①小爱音箱 Ultra 播放指定音乐 ②打开触发插座
2. 助手待命脚本 `scripts/light_show_watcher.py` 轮询该插座（prop/get，1-2 秒一次）→ 检测到 ON → 跑灯光秀 → 结束恢复灯并把插座复位
3. 实测链路延迟：插座 ON → 脚本检测到 ≈1 秒（轮询 2s）；检测 → 首拍 = `--show-delay`（**默认 5.0s**，按"小爱从收到指令到出声 5-7 秒"标定，见「音乐↔灯光 同频标定」）

**调参不生效时先查"参数 vs 常量"**：`light_show_watcher.py` 的 argparse 收了 `--show-delay`，但函数体里曾把模块常量 `SHOW_DELAY` 传给子进程 → **传参被静默忽略，怎么调都没反应**（本项目为此白跑一轮）。改任何"延迟/阈值"参数后，先 grep 确认该参数真的被下游读取，再去怀疑标定值不对。

**待命启动时先读一次信号灯**：若启动时它已是 ON，**只复位、不开演**（ON 只代表上次残留；立即触发会在用户没准备时突然闪灯，本项目踩过）——只等"上升沿"会漏掉这一次（本项目踩过）。

**待命纪律**：不要整天挂着轮询（每 2 秒一次 = 7200 次/4 小时云端调用）；用户说「**待命**」时再挂一段（`--minutes 30`），录完即停。

**音乐与灯同频（三层，按成本从低到高）**：
1. **BPM 实测，不靠猜**：`/opt/data/scripts/detect_bpm.py --media <录音或带声视频>` —— 自相关初筛 + 拍点线性回归精修，实测精度达 149.00 BPM / 首拍 0.00s。换歌、换版本（原版/DJ版/加速版）都以用户实际播放的文件为准
2. **启动时间差标定一次**：音乐由音箱本地播放、脚本不知其确切起点（实测出声比指令晚 **5-7 秒**，浮动 ±1-2 秒是固定补偿的天花板）→ 让用户录一段**带声音的视频**（画面含灯），同时提取"灯亮灭曲线"与"音频节拍曲线"求差，得到精确到 0.1s 的 `--delay`；同歌同音箱后每次误差 ±0.3s 内
3. **彻底方案（异地部署下不成立）**：把音乐交给助手推流，前提是助手能碰到音箱所在局域网；NAS 异地 → 除非在**家里**放一台常开小设备（旧手机/平板/树莓派 + xiaomusic/蓝牙）并与 NAS 组隧道，否则这条路走不通（见「中枢网关识别」节）

**端到端自测手法**：`light_show_watcher.py --test-fire --minutes 1 --bars 4` —— 脚本自己把信号灯打开，模拟用户口令，验证"检测→开演→复位"全链路，不需要用户配合。

触发设备选型：可读可写 + 不接关键负载（本项目用阳台电蚊香液 `lumi.plug.v1`，用户已同意）。细节与备选路径见 `references/music-rhythm-lighting.md`。

## 演出的停止与状态恢复（用户硬要求：停止要立刻 + 还原成开演前的样子）

用户明确要求：**任何灯光秀都要能"一句话立刻停"，并把灯恢复成开演前的状态**。落地四件事，缺一不可：

1. **开演前存快照** → `/opt/data/cache/light_show_state.json`（三灯各自 did/siid/piid/值 + 客厅灯渐变设置）。恢复的是"用户开演前的样子"（可能本来就有一盏开着），**不是**无脑全关
2. **停止标志优先于杀进程** → `touch /opt/data/cache/light_show.stop`：工作线程在每个事件前检查，0.2s 内停手；**不要靠 `pkill`**——默认 SIGTERM 不执行 finally，灯会卡在半闪状态
3. **信号处理兜底** → 脚本注册 SIGTERM/SIGINT → 置标志 → 走同一套恢复逻辑
4. **停止脚本复核** → `/opt/data/scripts/light_show_stop.py`：下标志 → 等演出收尾（最多 3s）→ 进程仍在就发 SIGTERM → **再按快照强制恢复一遍** → 回读复核并打印结果

实测（演出跑 6 秒后下停止）：标志生效 <1s，日志 `收到停止指令 → 已恢复原状态`，复核三灯与渐变均为原值、无残留进程。

**领普开关写入必须重试**：`/miotspec/prop/set` 外层 `code:0` 但**属性级 `result[0].code=1`** 表示未生效（首次常失败）→ 对 linp.switch.* 的写操作都要检查属性级 code 并重试一次，否则出现"命令返回成功但灯没关"（本项目就是这样卡住停止的）。

## 中枢网关识别（本地化硬件前提）

- 小米路由器 6500 Pro = `xiaomi.router.rd08`，**内置中枢网关**（用户家 <LAN_IP> 主路由，已具备本地化条件）
- rd15 = 小米路由器 BE3600 2.5G
- 独立中枢网关 model 为 xiaomi.hub.*；小爱音箱 Pro 可作中枢从网关
- **容器网络限制（根因已更正：不是 Docker，是异地部署）**：NAS 与家庭网络不在同一地点 → 内网 192.168.31.x 全部不可达（路由器/摄像头/音箱本地 IP 超时），**改 host 网络/macvlan 无效**。→ 本地直连路线（miIO 局域网协议、xiaomusic 推流、摄像头 RTSP）走不通，只能走云 API；要本地化必须在家里放常开设备再与 NAS 组隧道。设备本地 IP 与 miIO token 在 `/home/device_list` 响应里（`localip`/`token` 字段，属凭据，勿外泄）

## 登录流程（凭据过期时，30天一续）

完整流程固化在 `/opt/data/full_login.py`，四步：

1. **step1** GET `account.xiaomi.com/pass/serviceLogin?sid=xiaomiio&_json=true`（带 `deviceId`+`sdkVersion=3.8.6`+`passToken` cookies）→ 拿 `_sign`/`callback`/`qs`
2. **step2** POST `pass/serviceLoginAuth2`（user/hash=MD5大写/callback/qs/_sign/_json）→ 返回 **ssecurity + location**（前提：deviceId 已验证）
3. **step3** GET location（STS URL）→ 响应 cookies 拿 `serviceToken`
4. **step4** 用 ssecurity 签名调 `api.io.mi.com`（见 mijia_api.py）

**已验证 deviceId 的来源**：首次需浏览器走短信验证码登录（见下），登录成功后从浏览器 cookie 取 `deviceId`/`passToken` 复用。

## 浏览器登录（首次/验证码流程）

- **CDP 浏览器**：Hermes 自带 `/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell`，启动脚本 `/opt/data/start_cdp.py`（--remote-debugging-port=9222，后台运行），browser_exec 自动连接
- **流程**：小米登录页 headless 会被"环境安全检测"卡死 → 切 `fe/service/login/phone` 手机号登录 → 发短信验证码（用户提供）→ 过协议确认 → 系统要求再验证密码（verifyPwd）→ 跳 STS 拿 serviceToken
- 登录后浏览器 cookie 全集在 `/opt/data/cache/browser-use/workspace/*/mijia_all_tokens.json`（含 deviceId/passToken/serviceToken/identity_session）

## 关键坑（血泪）

1. **psecurity ≠ ssecurity**：serviceLogin 响应里的 `psecurity` 不能用于签名（invalid signature）。必须从 serviceLoginAuth2 成功响应的 `ssecurity` 字段取
2. **新 deviceId 必触发验证**：serviceLoginAuth2 返回 code=0 + notificationUrl 而非 location → 说明 deviceId 未验证。必须先浏览器完成验证，之后**复用同一 deviceId** 才直接成功
3. **API 签名**：`api.io.mi.com` 需要 RC4 签名（micloud miutils `gen_enc_signature`/`generate_enc_params`），请求头必须带 `MIOT-ENCRYPT-ALGORITHM: ENCRYPT-RC4`；响应也是 RC4 加密，用 `signed_nonce(ssecurity, _nonce)` 解密
4. **MIoT 路径全 404 + 路径前缀坑**：`/v2/device/get_prop`、`/miot/device/get_prop` 不存在；`mc.api(path)` 的 API_BASE 已含 `/app`，**传 path 不要带 `/app` 前缀**（`/app/scene/list` → 404，`/scene/list` → 200，白浪费多轮）。设备控制走 **miIO rpc**（`POST /app/home/rpc/{did}`，method=get_prop/set_power）或 **miotspec** 端点（灯具）
5. **lumi 网关子设备**（did 形如 `lumi.158d...`）：`get_prop` 报 `Method not found` → 需网关转发（未解决，WiFi 直连设备无此问题）
6. **headless 反爬**：小米登录页会卡"环境安全检测"，密码登录不可行；手机号+短信验证码可绕过
7. **curl/requests 直接调 serviceLogin 未带登录 cookie 返回 70016** → 必须带 passToken cookie 才返回 code=0

## 参考

- 老库 python-miio/micloud 的登录已全部失效（OAuth2 96006）；但 **micloud miutils 签名函数仍有效**，直接复用
- hass-xiaomi-miot（al-one）的 xiaomi_cloud.py 是 2026 最新登录实现参考，已下载到 `/opt/data/xiaomi_cloud.py`
- 认证探针新通道 `api2.mina.mi.com/admin/v2/device_list`（serviceToken cookies，无签名）——STS 发的 serviceToken 对它无效（401），仅作参考

## 本地化/自动化升级方向（HA 迁移调研）

用户已提出"本地中枢网关化 + AI 代设自动化"方向，完整方案对比、官方集成关键事实、部署步骤草案见 `references/home-assistant-migration-plan.md`（2026-09-05 调研，待部署验证）。核心结论：NAS 跑 HA + 小米官方集成（XiaoMi/ha_xiaomi_home）+ ha-mcp 接 Hermes；只导入 A 房设备。
