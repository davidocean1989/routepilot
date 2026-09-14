# RoutePilot｜Technical Spike 02：多点 Distance Matrix 验证（重新执行版）

项目：Davidocean · AI Career / RoutePilot  
重跑日期：2026-09-14（Asia/Shanghai）  
状态：**PARTIAL — 真实连接及工具发现成功；有效矩阵测试因缺少 Key 阻塞。**  
阶段：等待鉴权补齐及主任务归档决定。未进入 Spike 03，未执行优化算法。

## 1. 结论与历史边界

本次通过 Python MCP 客户端连接腾讯官方 SSE 服务，实际执行 initialize、tools/list 和三次 matrix 调用。当前确有直接 matrix 工具，不需要以批量 directionDriving 代替原生矩阵。

三次矩阵调用均返回 is_error=true、Invalid Key，没有成功的距离或时间值。因此不能确认当前账号是否能支撑 RoutePilot V1；发送了某种请求形状也不代表该数量已被接受。

本地存在 2026-09-12 的历史成功报告和证据。旧报告已原样保存在 [历史报告备份](spike-02-evidence/rerun-2026-09-14/historical-report-2026-09-12.md)，旧 JSON 未改写；本次不把历史成功算入重跑结果。旧报告中的后续 Spike 建议不构成本任务授权。

## 2. 测试环境

- macOS 15.7.9，x86_64；Python 3.12.14；MCP SDK 2.2.0。
- 临时环境：/private/tmp/routepilot-spike02-rerun-venv。
- 腾讯服务：TencentMapMCPWebService 1.2.0；协议 2025-11-25。
- SSE 连接模板：https://mcp.map.qq.com/sse?key=<KEY>&format=1。
- 本次 Key 为空。当前工具目录没有腾讯工具，相关环境变量、本地项目 .env 和 Codex MCP 配置未发现腾讯连接；没有从历史聊天挖掘密钥。
- 首次沙箱连接出现 DNS ConnectError，获得联网执行权限后成功连接。该错误是本地限制，不是腾讯服务故障。
- 联网测试开始：2026-09-14 16:35:27 +08:00；证据时间为 UTC。

证据是 SDK 序列化结果，非逐字节 HTTP 报文。原始请求、响应、时间、耗时、握手和完整工具列表均已保存。

## 3. 测试地点

坐标沿用历史腾讯 POI 结果 [points.json](spike-02-evidence/points.json)，本次没有刷新。GCJ-02，纬度在前；车站和停车场用于可复现测试，不表示重新核验了车辆入口。

| 简称 | 地点 | lat,lng |
|---|---|---|
| 杭州 | 杭州东站 | 30.291331,120.212998 |
| 南浔 | 南浔古镇1号停车场-入口 | 30.869188,120.430771 |
| 乌镇 | 乌镇西栅景区1号停车场-入口 | 30.745906,120.488840 |
| 西塘 | 西塘古镇景区第一地上停车场 | 30.938980,120.888689 |
| 上海 | 上海虹桥站 | 31.194106,121.320666 |

## 4. 真实测试案例及返回

| 案例 | 实际调用 | 返回 | 耗时 |
|---|---|---|---:|
| C01 | initialize | 成功，取得服务版本 | 131.95 ms |
| C02 | tools/list | 成功，15 个工具，含 matrix、directionDriving | 167.54 ms |
| C03 | matrix，杭州→南浔，1×1 | Invalid Key | 98.37 ms |
| C04 | matrix，南浔→杭州，1×1 | Invalid Key | 24.07 ms |
| C05 | matrix，五地点作两侧，5×5 | Invalid Key | 96.13 ms |

请求依次发送，每次工具调用结束后等待 2 秒。monotonic 耗时不含建连与等待；**以上矩阵耗时仅为鉴权失败延迟，不能用作成功 API 性能基线。**

matrix 实际必填字段是字符串 from、to、mode，不是 origins/destinations。from/to 分别表示起点和终点集合；多点以分号分隔，mode=driving。当前 schema 没有数量上限或 output_schema。完整 5×5 请求参数见 live-probe.json events[2]。

三次调用的共同关键返回：

```json
{"content":[{"type":"text","text":"Invalid Key"}],"structured_content":null,"is_error":true}
```

没有业务 JSON、result、rows、distance、duration 或 request_id。不能直接把错误文本当作 JSON 矩阵解析。

## 5. 能力验收表

| 项目 | 本次结论 | 证据边界 |
|---|---|---|
| 直接 Matrix Tool | 是，matrix | 本次工具发现实测 |
| origins 支持数量 | 未确认 | 发送过 1、5；均鉴权失败 |
| destinations 支持数量 | 未确认 | 发送过 1、5；均鉴权失败 |
| 成功返回结构 | result.rows[i].elements[j] | 官方参考；本次未成功取得 |
| distance 单位 | 米 | 官方参考；待本次成功响应核对 |
| duration 单位 | 秒 | 官方参考；区别于驾车规划的分钟 |
| A→B 与 B→A | 本次无法比较 | 两方向均鉴权失败 |
| 成功 API 延迟 | 未取得 | 不以错误延迟替代 |
| 错误处理 | Invalid Key 为 MCP 错误文本 | 三次真实返回 |
| 配额/频控 | 未验证 | 无有效 Key，未查控制台 |

2026-09-14 核对 [TencentLBS 官方 API 参考](https://github.com/TencentLBS/tencentmap-webservice-skill/blob/main/references/api-direction.md)：一对多 ≤200 个；多对多每侧 ≤50，点对乘积 ≤625；矩阵距离为米、时间为秒。该参考未单独明确多对一上限，本次不补写实测值。单元 status=4 时可能是直线距离，应排除于驾车成本数据。直接打开官网矩阵页失败，本段来源是官方 GitHub 参考，不是本次官网页面实取。

历史原始 [matrix.json](spike-02-evidence/matrix.json) 曾记录杭州→南浔 84018 米/4211 秒，反向 83112 米/4611 秒，以及非零对角线。这只是旧快照的差异，不能冒充本次成功数据。历史上限测试也曾被频控遮挡，不能据旧记录确认硬上限。

## 6. 替代方案及错误处理设计

当前已有 matrix，缺少 Matrix Tool 的条件不成立。优先在有效 Key 下测试原生矩阵，不用 directionDriving 绕过鉴权或额度问题。

若未来部署确实不暴露 matrix，可逐个有向点对调用 directionDriving：五地点需 5×4=20 次，跳过同索引对角线，不把反向值复制过来。保留原始响应、路线选取规则、坐标和时间戳；按驾车规划的分钟单位换算成秒后检查所有边完整性。此为备用设计，本次未执行该批量调用。

若原生矩阵大批次受限，可分五个 1×4 批次，按点对工作量节流。历史成功节流参数不代表当前账号保证容量；收齐全部有向边后才形成快照，不无标记拼接旧数据。

错误检查顺序：传输异常 → MCP is_error → 业务 JSON/status → 维度和单元合法性。鉴权失败停止并修正配置；参数错误不原样重试；频控在确认额度后有限退避并缩批；日配额耗尽停止。无路、缺失 duration 和失败单元保持缺失，不补零或直线距离。归一化时仅可按模型定义把同索引的逻辑停留成本设为零，并保留原始对角线。

## 7. 对 RoutePilot V1 的影响及补测

接入方向具备可行性，当前服务确实提供原生 matrix。但本轮未取得有效成本数据，**不能据本次重跑批准 V1 数据能力验收通过**。必须补齐有效 Key，才能确认完整矩阵、方向差异、成功延迟及实际调用容量。

需要用户提供本机私人 Key 配置文件路径，或连接可调用的腾讯 MCP。此前已提出该缺失信息请求；没有收到时不猜测凭据。

待补测：刷新五个 POI；1×1 双向、1×4、4×1、2×2、5×5；必要时拆分取得完整 20 条非对角边；重复小样本验证结构与成功延迟；无效模式、坐标及必填参数错误；在账号额度允许时分别验证最大合法值及超限值，避免频控遮挡边界。配额依控制台及适量实测确认，不进行额度耗尽测试。以上是待办，不是已执行记录。

## 8. 正式证据与复现

- [本次完整 MCP 证据](spike-02-evidence/rerun-2026-09-14/live-probe.json)
- [沙箱网络失败](spike-02-evidence/rerun-2026-09-14/sandbox-network-attempt.json)
- [本次客户端](spike-02-evidence/rerun-2026-09-14/run_probe.py)
- [历史文件哈希清单](spike-02-evidence/rerun-2026-09-14/historical-manifest.json)
- [历史报告原样备份](spike-02-evidence/rerun-2026-09-14/historical-report-2026-09-12.md)
- [Final Archive Summary](spike-02-evidence/rerun-2026-09-14/final-archive-summary.md)

在项目根目录用临时环境的 Python 执行 run_probe.py；可从私人配置向进程提供 TENCENT_MAP_KEY，密钥不写共享文件。再次运行前须保存旧运行目录，因脚本会覆盖 live-probe.json。脚本仅执行本报告三次矩阵调用，完整验收还需第 7 节补测。

本次只保存本地 Spike 02 文件，未推送 GitHub；sources 和其他 Spike 未修改。
