# MVP Build 交付记录

分支：feat/mvp-build。基线：08afd47fd05019e43e0dd544e64150f33397ab4c。

## M0

计划先于产品代码单独提交并推送：fb6473ee21c288bcade03e0654155935eca9c01f。

## M1

FastAPI 应用工厂、Trip/Pydantic 校验、SQLite WAL、创建/读取、健康检查、统一错误与请求编号。编辑令牌只保存 SHA-256，读取接口不暴露令牌。SQLite 更新使用 revision 条件更新，后续流程复用。

测试：`python -m pytest tests/test_api.py -q`，13 passed；覆盖重建应用后持久化、非法输入、未知行程、密钥不外泄等。

依赖：使用隔离 Python 3.11 环境，安装版本锁定在 requirements.lock。cryptography 最新源码包在本机缺 OpenSSL 编译依赖，使用预编译兼容包 48.0.1；未要求全局编译工具。上游 Starlette 对 AnyIO 的弃用提示由精确测试 warning filter 过滤。

下一步：M2 迁入已验证优化器并实现腾讯 MCP 数据与行程工作流。

## M2

腾讯 MCP SSE 客户端、工具响应业务状态校验、3 次以内尝试、串行间隔、分行有向矩阵、POI 城市筛选与确认、真实道路差分折线及分钟→秒转换。Trip resolve/confirm/optimize 已接入，结果只读，冲突返回 409；上游失败保留已确认状态，缺道路几何时保存排序及明确警告。

原优化器、11 项原测试与原复核脚本从同项目本地归档逐字节迁入，见 `mvp-evidence/optimizer-provenance.json`。没有改算法。历史演示使用仓库 2026-09-14 真实采样矩阵，标记 historical_demo，未知地点不替换，实时服务失败不会回落演示。

验证：55 Python tests、64 原算法 subtests 通过。包含限流恢复、鉴权不重试、超时、矩阵缺边、方向性、单位、polyline、城市筛选、权限、状态机、持久化、版本冲突和流程失败保留。M1 HTTP smoke 已通过。M2 HTTP smoke 命令：`python scripts/smoke.py http://127.0.0.1:8766 --full`。

当前进程 TENCENT_MAP_KEY 未配置；本轮未真实调用腾讯，不将契约测试当作在线联调。默认真实模式缺配置明确 503。浏览器凭证与服务端凭证要求不同值。

下一步：M3 三页面、腾讯 JS 地图、NavigationAdapter 与浏览器交互验收。

## M3：本地最小闭环完成

- 输入页：简单句式拆分、可编辑起点/3–8途经点/终点，添加/删除/调整顺序，最快/最短与开放/固定/返回起点选择。
- 确认页：显示候选名称/城市/地址、逐点明确选择；重新读取/重试能恢复 draft/resolved/confirmed 状态。
- 结果页：原/优化顺序、双指标及带正负号含义的收益、每段成本、采样时间；持久 Trip 只读链接、复制、手动切段/刷新恢复。
- 腾讯 GL SDK 适配：编号 Marker、真实道路 MultiPolyline、视野 bounds、转义后字符串 InfoWindow；无 Key/加载失败清晰降级，演示仅绘制标注的顺序虚线。
- NavigationAdapter/TencentMapAdapter 已实现逐段 qqmap URI。BaiduMapAdapter/AmapAdapter 保留明确未启用的接口；本阶段不承诺它们已经支持导航。未做整条路线交付。
- 请求 JSON 日志默认开启 INFO，包含 request_id、工具/状态、耗时、trip_id、顺序和点击。省略完整用户地址、原始输入和上游异常 URL，避免凭证/个人行程进日志。点击不计作导航成功。

### 最终验证

- Python：59 tests passed，64 原算法 subtests passed。
- JavaScript：9 tests passed，含真正调用 RouteMap.render 的严格 SDK 合约测试（并非在线 SDK）。
- HTTP：健康、创建、读取、解析、确认、优化、结果重读闭环通过。
- 浏览器：三个页面真实 UI 流程通过；390px/1280px 布局与刷新恢复通过。详情 `mvp-evidence/browser-checks.md`。
- 独立审查：两个 P2 已修复并复核；没有未处理的已知 P1/P2。
- 密钥：仓库不写真实凭证；本轮 `TENCENT_MAP_KEY`、`TENCENT_JS_KEY`、`TENCENT_NAV_KEY` 未配置。

### 里程碑提交

| 里程碑 | Commit |
|---|---|
| M0 计划先行 | fb6473ee21c288bcade03e0654155935eca9c01f |
| M1 后端与 SQLite | 4d3be29137e4a5b4477750d319cb60203a0f7135 |
| M2 地图与优化 | 2a6aaef87a2013701ec06bb67d119d9b972770a6 |
| M3 三页与最终验证 | 本文件当前提交；最终 SHA 在交付回报中列出 |

### 下一步（保持 MVP 范围）

在私有运行环境配置有效腾讯服务端 Key，以及两个与服务端隔离的浏览器可见凭证，按 mvp-run.md 做真实地点→矩阵→道路→浏览器地图联调。之后再为 HTTPS 部署与手机闭环做验收；未把目前离线演示标为线上产品、腾讯在线全链通过或完整 V1 通过。

通用自然语言 Agent、全路线/多厂商导航、所有 V1 成功率与性能指标均非本阶段已完成功能。3–8 waypoint 的算法支持已验证，但真实10地点采集性能和配额尚未实测。后台未加入账号系统或公网限流；当前只按本机/受控环境、单进程运行交付。

## 核对的官方接口

- [腾讯 MCP 接入](https://lbs.qq.com/service/MCPServer/MCPServerGuide/userGuide)
- [腾讯 Matrix / Direction 单位及道路解码](https://github.com/TencentLBS/tencentmap-webservice-skill/blob/main/references/api-direction.md)
- [腾讯 GL 折线](https://lbs.qq.com/webApi/javascriptGL/glDoc/glDocVector)
- [腾讯 GL 信息窗口（字符串参数）](https://lbs.qq.com/webApi/javascriptGL/glDoc/glDocInfo)
- [FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)
