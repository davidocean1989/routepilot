# 一趟跑完｜MVP Implementation Plan

日期：2026-09-15。开发基线：`08afd47fd05019e43e0dd544e64150f33397ab4c`。

**Goal:** 实现输入 → 地点解析与人工确认 → 真实矩阵 → 确定性排序 → 持久结果 → 地图与逐段导航的最小运行闭环。

**Architecture:** 单个 FastAPI 进程提供同源 API 与 HTML/CSS/Vanilla JS；SQLite 保存完整 Trip JSON、版本和结果。腾讯 MCP 是真实数据源，优化器沿用 Spike 03；离线演示使用明确标注的历史快照，真实服务失败绝不自动切换演示数据。

**Tech Stack:** Python 3.11+、FastAPI、Pydantic、SQLite 标准库、MCP Python SDK、httpx/pytest（测试）、腾讯地图 GL JS SDK。无 React、Redis、Celery 或额外数据库。

**Spec:** [00 项目立项书](00-project-charter.md)、[01 用户旅程](01-user-journey.md)、[02 PRD](02-prd.md)、[03 技术设计](03-technical-design.md)。本计划限定本次第一阶段，不宣称整个 V1 产品已验收。

执行方式：本会话按 `superpowers:executing-plans` 逐个里程碑实现；使用测试先行及完成前验证工作流。用户已授权先提交计划再实现及分阶段 push。独立 checkout `routepilot-build/`，分支 `feat/mvp-build`，保留 main 及所有历史材料。

## 1. 已确认依据与范围裁剪

| 依据 | 实施决定 |
|---|---|
| Spike 01 | SSE `https://mcp.map.qq.com/sse?format=1`，服务端 Key 注入；候选 POI 必须用户确认，不能把模糊地名自动改成入口 |
| Spike 02（2026-09-14） | 单次 5×5 返回 120；五个 1×5 成功。按行串行取矩阵、节流、最多重试两次；保留有向边、米/秒、采样起止时间、非原子标志；拒绝缺失值 |
| Spike 03（2026-09-14） | 直接复用本地已验证 `routepilot/optimizer.py`；3–8 个可排列途经点，不含起终点，支持开放/固定/回到起点，fastest/shortest；并列规则不变 |
| Spike 04（2026-09-14） | 导航与路线规划分开；先逐段交接。腾讯 passes 的官方能力不等于本 MVP 全路线实机通过；高德/百度保留 Adapter 边界 |
| Spike 06 本地归档 | iPhone Safari → 腾讯 App 正确起终点并开始导航有历史用户反馈；微信内直达失败。仓库未同步此报告，实施时加入来源说明，不新增通过结论 |

仓库基线只包含文档与实验记录，未包含 Spike 03 报告引用的优化器及测试。M2 将从同一项目本地归档复制源码与原测试，核对内容并复跑，记录来源哈希；不把迁入旧代码描述为新算法研发。

### Global Constraints

- 品牌：**一趟跑完**；副标题：**一天跑 6 个地方，怎么走最顺？**
- 只支持驾车，3–8 个可排列途经点；最大 10 个不同地点。服务端硬性校验。
- 所有路线成本来自腾讯，距离米、时间秒，GCJ-02。仅在优化输入副本中归零对角线。
- 最快/最短是当前分批成本快照下的顺序最优，不承诺未来出发时刻、全道路最短或导航 App 保留道路与 ETA。
- 输入页先提供简单地点表单，并支持示例句式的确定性拆分；不接新的 LLM 供应商。无法解析必须转可编辑字段，不猜地点；通用自然语言理解仍是 V1 后续工作。
- 显式选择终点模式：固定终点、结束在任一途经点、回到起点。保留原始顺序和原始文字。
- 服务端 Key 永不返回客户端；JS SDK 与腾讯导航分别使用独立浏览器可见凭证配置，默认空，不复用服务端 Key。
- 不增加推荐、景点介绍、时间窗、停留时间、加油/充电、酒店、门票、动态重排或账号系统。
- 本阶段交付本地可运行服务与 GitHub 分支，不替换现有导航实验网站。匿名 Trip 链接持有者可读取行程；写操作使用创建时返回的独立编辑令牌，令牌不出现在分享 URL。

## 2. 目录与职责

```text
app/
  main.py                 应用工厂、生命周期、静态页、请求日志
  config.py               环境变量配置，三种凭证隔离
  errors.py               统一安全错误结构
  models.py               TripInput / Place / Trip / Matrix / Result
  database.py             SQLite 初始化、读取、带版本比较的原子保存
  api.py                  创建、解析、确认、优化、结果及事件 API
  services/
    trips.py              状态流转与优化编排
    maps.py               MapProvider 协议、腾讯数据校验与单位转换
    mcp_client.py         SSE 会话、工具响应解包、节流、重试
    demo.py               显式历史样本演示，未知地点直接报错
routepilot/
  optimizer.py            Spike 03 原算法（迁入，保持独立）
web/
  index.html              输入页
  confirm.html            候选地点、地址确认与重选
  result.html             顺序、指标、地图、分段导航、复制链接
  styles.css              手机优先布局
  common.js               API、状态、错误、复制辅助
  input.js / confirm.js / result.js
  map.js                  腾讯 SDK 加载、标记、真实道路折线、视野
  navigation.js           NavigationAdapter 与腾讯逐段 URI；其他厂商接口
tests/
  test_api.py             HTTP 流程、校验、持久化、权限、版本冲突
  test_maps.py            MCP 包装、矩阵维度/单位/方向、错误与重试
  test_optimizer*.py      原测试与真实快照回归
  test_workflow.py        完整演示闭环与故障保持
  web.test.cjs            前端纯逻辑与导航协议
scripts/
  smoke.py                运行中服务 HTTP 冒烟
docs/
  04-mvp-implementation-plan.md
  mvp-build-report.md     里程碑、运行方法、证据与未验收边界
  project-status.md       追加当前 MVP 状态，保留历史
pyproject.toml / requirements.lock / .env.example / .gitignore
```

## 3. 数据与 API 合约

Trip 使用 UUID、UTC 时间、递增 revision，状态为 `draft → resolved → confirmed → optimized`。失败保持上次成功状态与结果；重解析清除确认及旧结果。优化后的快照不可修改，重新规划创建新 Trip，保证分享结果稳定。

TripInput：`start: {query, city}`、`waypoints: [{query, city}]`、`end: {query, city}|null`、`end_mode: fixed|open|roundtrip`、`objective: fastest|shortest`、`raw_input`。城市可选，但存在时传给腾讯并在确认页展示返回行政区。Place 保存 `poi_id/name/address/city/lat/lng/coordinate_system`。

| 方法 | 路径 | 行为 / 状态码 |
|---|---|---|
| GET | `/health` | 应用与数据库可用，200 |
| POST | `/api/trips` | 校验输入并保存 draft，201，返回 trip 与 edit_token |
| GET | `/api/trips/{id}` | 读取行程与结果，200；未知 404；不返回编辑令牌 |
| POST | `/api/trips/{id}/resolve` | 查询全部候选，保存 resolved；缺少候选时返回可处理错误 |
| POST | `/api/trips/{id}/confirm` | `{revision, candidate_ids:[...]}`，按原顺序选择服务端已保存候选；必须全量确认且不重复 |
| POST | `/api/trips/{id}/optimize` | `{revision}`，仅 confirmed；保存原始/优化顺序、双指标及带 polyline 的分段 |
| POST | `/api/trips/{id}/events` | 仅记录允许的 share_click/navigation_click，点击不当作导航成功 |
| GET | `/api/config` | 仅浏览器公开设置与演示标志 |
| GET | `/t/{id}` | 只读结果页，可重新打开，无需重新输入 |

写操作除创建外使用 `X-Trip-Token` 与 revision；冲突 409、非法输入 422、未授权 403、上游超时 504、业务/矩阵错误 502、未配置 503。统一响应 `{error:{code,message,request_id}}`，不返回上游 URL、Key、原始响应或异常堆栈。

MCP 会话在同一异步任务内打开、调用、关闭，避免跨任务退出 SSE 的取消作用域。一次解析/优化共享一段会话；全局限流锁避免同进程并发耗尽 QPS。单进程是本阶段运行约束。矩阵请求维度 1×N，批次采样非原子；上游 120/429/5xx/超时最多重试两次，鉴权和参数错误不重试。优化请求有整体预算，超过时明确失败，不保证 10 地 60 秒 SLA。

地图详细路线单独查询并记录其时间（分钟转秒）、距离与采样时间，不覆盖矩阵用于优化的成本。真实 polyline 不可得时保留成功排序及明确警告，不用点间直线冒充道路；演示模式仅显示标注为顺序示意的连线。

## 4. 里程碑与逐步验收

### M0：计划先行

- [x] 阅读 00–03 和 Spike 01–04/06，记录差异与边界。
- [x] 生成本文件，核对用户 11 项目标均映射到 M1–M3。
- [x] 单独提交并推送计划，记录 SHA；之后才写产品代码。

### M1：可运行后端与 SQLite

- [x] 新建 `tests/test_api.py`，先断言 `POST /api/trips` 返回 201、再换应用实例用相同 SQLite 路径读取相同 Trip，先运行确认缺失实现失败。
- [x] 实现配置、模型、SQLite、应用工厂与创建/读取端点；连接按操作打开，不共享跨线程连接；JSON 严格序列化，编辑令牌只存哈希。
- [x] 覆盖 2/9 个途经点拒绝、空白名称、非法 objective、未知 Trip、持久化、错误结构与健康检查。
- [x] `python -m pytest tests/test_api.py -q` 通过；启动 uvicorn 并 HTTP 检查 health/create/get。
- [x] 更新运行说明、commit/push，报告 SHA、功能、测试与下一步。

验收示例：`POST /api/trips` 传杭州起点、乌镇/西塘/南浔三个途经点、上海终点；服务重启后 GET 内容保持，源目录参考资料不变。

### M2：地图、确认、优化与结果 API

- [x] 迁入旧优化器与测试，运行旧回归确认基线；保留源码哈希。
- [x] 先写 provider 契约测试：用真实 MCP 响应外壳模拟 120→成功、非法 Key、超时、缺行缺边、非对称矩阵、非零对角线、direction 分钟与差分 polyline；确认新包装层缺失时失败。
- [x] 实现 MCP 客户端、数据 Provider 与独立演示 Provider；演示明确引用 2026-09-14 历史矩阵。
- [x] 先写流程测试：未确认禁止优化、伪造候选拒绝、重复地点拒绝、过期 revision 拒绝、上游失败不写部分结果、重新打开结果相同。
- [x] 实现 resolve/confirm/optimize，复用 `optimize_route(0, waypoints, end, time_matrix, distance_matrix, objective)`；保存成本快照、时间范围和结果。
- [x] 真实历史回归：原杭州→乌镇→西塘→南浔→上海，fastest 12954 秒/229985 米；shortest 13233 秒/219289 米；不能把历史数值写作实时结果。
- [x] 运行完整 Python 测试，使用离线显式演示模式完成 HTTP 闭环；若提供私有环境 Key 则单独真实 smoke，不打印凭证，不假装凭证已配置。
- [x] 更新状态、commit/push 并报告。

### M3：三个页面、腾讯地图与导航接口

- [x] 先写前端可验证逻辑测试，检查示例输入解析、导航协议/lat,lng 编码、非法点、分享 URL 无令牌、进度不自动推进。
- [x] 输入页：一句话示例拆分和可编辑字段，添加/删除/上下调整 3–8 途经点，目标与终点模式。解析失败展示字段供用户修正。
- [x] 确认页：全部候选显示名称、城市、地址；不默认替用户确认；可回输入修改并创建新 Trip；提交完整选择后执行优化。
- [x] 结果页：顺序、总时间/距离、与原顺序差值、每段成本、采样提示；加载腾讯 GL SDK、编号 Marker、InfoWindow、道路 Polyline 与 fitBounds。
- [x] 实现 NavigationAdapter 合约与腾讯逐段原生链接；高德/百度保留可替换接口及明确未启用状态，不伪造可用链接。复制目的地、微信浏览器打开帮助、手动切段并在 URL 保留段号。
- [x] 处理加载中、失败重试、过期确认、分享只读恢复、地图 Key 缺失/SDK 加载失败；通过 textContent 渲染不可信文本。
- [x] `python -m pytest -q`、`node --test tests/web.test.cjs`、JS 语法检查、运行中 HTTP smoke；实际浏览器验证完整流程与手机宽度布局。SDK 合约测试与真实在线渲染分开记录。
- [x] 更新 README、project-status、mvp-build-report；最终 review、commit/push，核对远端 SHA。真机/在线地图未运行的项明确列待验收。

## 5. 完成定义

无 Key 时可显式启动历史演示完成闭环；默认真实模式缺 Key 会明确报配置错误。配置合法腾讯服务端 Key 后，产品代码可调用同一已验证 MCP 工具，而非让用户手工拷贝成本。所有输入与结果落库，分享读取稳定；有明确失败路径、基础日志及可重复测试。

本次软件完成不等于线上服务部署、所有地图/手机兼容、实时地图联调、真实流量性能或整个 V1 验收。每次里程碑报告必须分清自动测试、历史证据、本次真实联调与待验收事项。

## 执行回填

M0–M3 软件实现和本地验收完成。勾选表示相应实施步骤已处理，条件性的真实腾讯 smoke 因未配置 Key 没有执行；腾讯在线底图、道路、真机兼容和部署均不记为通过。准确测试范围见 mvp-build-report.md 与 mvp-evidence/browser-checks.md。
