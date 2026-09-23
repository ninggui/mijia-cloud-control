# Home Assistant 迁移方案调研（2026-09-05，待部署验证）

用户目标：本地中枢网关化 + AI 补全/代设自动化。调研已完成，部署待用户确认两点（是否有中枢网关、NAS 资源）。未落地前不要当已验证流程执行。

## 方案对比结论

| 方案 | 性质 | 角色 |
|---|---|---|
| **XiaoMi/ha_xiaomi_home**（官方集成） | 小米官方 HA 集成 | 主方案：设备接入 + 中枢网关本地化 |
| al-one/hass-xiaomi-miot | 第三方（~10K stars） | 备选：官方不支持的冷门机型补充 |
| AlexxIT/XiaomiGateway3 | 第三方（~11K stars） | 网关级纯本地（Zigbee/BLE/Mesh），非必需 |
| homeassistant-ai/ha-mcp | MCP server（75+ 工具） | AI 层：管理自动化（创建/修改/删除），让 Hermes 直接接管 |

**选定架构**：NAS Docker 跑 Home Assistant + 官方米家集成 + ha-mcp 接 Hermes（native MCP 客户端）。

## 官方集成关键事实（2026-09-05 调研）

- 仓库：`github.com/XiaoMi/ha_xiaomi_home`（~18.6K stars，官方持续更新）
- 安装：HACS 自定义仓库 或 git clone + `./install.sh /config`；要求 HA Core ≥ 2024.11.0
- 登录：OAuth 2.0（账号密码不交给第三方），支持多账号、数千设备
- **中枢网关本地化**：中枢网关固件 ≥3.4.0_000（或内置中枢软件 ≥0.8.0）的米家设备支持本地控制；无中枢则全部走云
- 本地+云端自动切换；同一局域网时也可用"小米局域网控制"（仅 IP 设备，官方不建议）
- 小米中枢网关 ZSWG01CM（四核+4GB）本地自动化：断网可用、毫秒级；米家 app 自动化可切"本地执行"，复杂逻辑用"极客版"

## 用户需求映射

1. **关全部灯漏灯** → HA 按 domain 整域调用（`light.turn_off` 覆盖全部灯实体），天然不漏；AI 可审计实体清单补全自动化
2. **云端自动化→本地中枢网关** → 米家 app 自动化切"本地执行"（需中枢网关）；HA 自动化本身跑在 NAS 本地
3. **运行/代设自动化** → Hermes 接 ha-mcp 的 manage_automation 工具（create/patch/delete/execute）
4. **AI 主动列优化方案** → 设备清单审计模式：列全灯/开关/传感器 → 检查自动化覆盖盲区 → 出补全方案给用户确认后写入

## 部署步骤草案（待用户确认后执行）

1. 绿联 NAS Docker 起 `homeassistant/home-assistant` 容器（/config 卷持久化，≥2G 内存、10G 空间）
2. HACS 装官方集成，米家账号 OAuth 登录，**只导入 A 房（<小区名>）设备，B 房（B房）不碰**（用户红线）
3. 确认中枢网关固件 ≥3.4.0_000；米家自动化逐个切本地执行
4. Docker 起 ha-mcp（有官方 Docker/HA add-on），Hermes config.yaml 注册 MCP server
5. 设备清单审计 → 补全自动化方案 → 用户确认 → 写入

## 建议的增量优化（用户未提但符合其思路）

- 离家/回家模式兜底：一键关全屋灯按域执行不漏
- 设备离线/异常告警 → 飞书推送（复用现有推送链路）
- AI 自动化定期审计：拉取自动化清单查覆盖盲区
- 保留现有 mijia-cloud-control 云 API 直控作为轻量双通道互备

## 待确认项

- 是否有小米中枢网关（或带中枢功能的路由器/中控屏）→ 决定本地化路径
- 绿联 NAS 剩余内存/硬盘 → 决定 HA 容器规格
