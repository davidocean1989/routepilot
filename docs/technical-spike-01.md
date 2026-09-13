# 04｜Technical Spike 01 — Tencent Location MCP

项目：Davidocean · AI Career / RoutePilot  
对外名：一趟跑完  
副标题：一天跑 6 个地方，怎么走最顺？  
验证日期：2026-09-11（Asia/Shanghai）  
状态：**最小链路验收通过；有效 Key 下的地点解析与真实驾车查询均成功。**

## 1. 目标与当前结论

最小链路：北京东坝 → 地点解析 → 北京国贸 → 地点解析 → 驾车路线 → 真实距离与预计时间。

已在本机 Python 环境连接腾讯官方 MCP。首轮无 Key 时 geocoder 返回 `Invalid Key`；用户提供 Key 后重测成功，取得两个地址的真实坐标，并用这些坐标取得驾车距离和预计时间。随后针对地名歧义增加了一个明确 POI 的补充样例。

**技术判断：腾讯位置服务通过本次最小技术验证，可作为 RoutePilot V1 的地图数据源。接入必须核对地点语义、筛选城市并转换时间单位。** 本次没有验证多点矩阵、长期稳定性、全时段准确度或商业额度，不代表这些项目已经验收。

未开发完整应用、地图页面、FastAPI、数据库或路线优化器；未更改 sources 下的参考文件，也未配置 WorkBuddy 本身。

## 2. 已完成的环境配置

选择用户允许的“可用开发环境”路径：本机 macOS + Python MCP SDK，连接腾讯托管服务，无需部署腾讯 MCP Server。

当前会话没有已挂载的腾讯地图工具。使用已有 uv 建立临时隔离环境，实际 Python 版本为 3.12.14，安装 MCP SDK 2.2.0。命令如下：

```sh
UV_CACHE_DIR=/private/tmp/routepilot-uv-cache uv venv /private/tmp/routepilot-spike-01-venv
UV_CACHE_DIR=/private/tmp/routepilot-uv-cache uv pip install --only-binary=:all: --python /private/tmp/routepilot-spike-01-venv/bin/python mcp==2.2.0
```

本次实测依赖版本另见 [依赖快照](spike-01-evidence/dependencies.txt)。临时环境可能被系统清理，后续可按上述命令重建；未改动全局 Python。

本次连接地址（没有 Key）：

```text
https://mcp.map.qq.com/sse?format=1
```

官方也支持 Streamable HTTP；本次只验证 SSE。`format=1` 请求原始 JSON 数据，`format=0` 为面向模型的语义化文本。详见[官方接入说明](https://lbs.qq.com/service/MCPServer/MCPServerGuide/userGuide)。

## 3. 首轮请求与返回（未提供 Key 的历史记录）

以下毫秒数为单次 MCP 方法调用耗时，不含建连时间，不是地图路线耗时，也不能当作性能基准。

| 阶段 | 实际调用 | 实际结果 | 耗时 |
| --- | --- | --- | --- |
| 传输探测 | GET /sse，不带 Key | HTTP 200，text/event-stream，收到 endpoint 和 ping | 未单独计量 |
| MCP 握手 | initialize | TencentMapMCPWebService，服务版本 1.2.0，协议版本 2025-11-25 | 64 ms |
| 工具发现 | tools/list | 返回 15 个工具，无下一页 | 171 ms |
| 起点解析 | geocoder，address=北京市朝阳区东坝 | is_error=true，文本 Invalid Key | 197 ms |
| 终点解析 | 计划 geocoder，北京市朝阳区国贸 | 未执行：上一步认证失败 | — |
| 驾车路线 | 计划 directionDriving | 未执行：没有真实坐标和有效 Key | — |

原始 SDK 序列化记录：

- [握手与完整工具定义](spike-01-evidence/unauthenticated-mcp.json)，UTC 15:36:07，即北京时间 23:36:07。
- [地址解析失败响应](spike-01-evidence/unauthenticated-geocoder.json)，UTC 15:36:41，即北京时间 23:36:41。

这些文件采用 SDK 的蛇形字段名，例如 `is_error`、`input_schema`，不是逐字节 HTTP 报文。

实际地址解析输入：

```json
{"address":"北京市朝阳区东坝"}
```

实际响应的关键字段：

```json
{
  "content": [{"type": "text", "text": "Invalid Key"}],
  "structured_content": null,
  "is_error": true
}
```

本次未产生业务状态码、地点匹配结果或路线数据。此前讨论中的 18.4 km、35 min 等数值均为示例，不属于本次结果。

## 4. 实测工具及最小调用顺序

工具列表包含 geocoder、placeSuggestion、placeSearchNearby、directionDriving、placeAlongby、placeDetail、matrix、reverseGeocoder、ipLocation、weather、directionWalking、directionBicycling、directionTransit、futureDrivingDirection、waypointOrder。

与本次相关的实际输入 schema：

| Tool | 参数 | 用途 |
| --- | --- | --- |
| geocoder | address：必填字符串 | 地址解析；首轮认证失败，有 Key 重测已成功 |
| placeSuggestion | keyword：必填；region：可选 | 地名有歧义时查询北京范围的候选地点；已在重测中调用 |
| directionDriving | from、to：必填字符串，格式 lat,lng | 两点驾车规划；已在重测中调用 |

重测采用的调用流程：

1. 重新 initialize → tools/list，确认当前工具定义。
2. geocoder({"address":"北京市朝阳区东坝"})。
3. geocoder({"address":"北京市朝阳区国贸"})。
4. 检查解析结果确实属于北京朝阳区，并保存地址、坐标和返回的匹配信息。东坝是区域名，国贸也可能指商圈、地铁站或建筑，不能把解析结果直接当成用户指定的入口。必要时使用 placeSuggestion 查询并明确具体地点；若改用地铁站等具体 POI，须在报告中记录测试用例调整。
5. 仅使用以上真实返回的坐标调用 directionDriving({"from":"起点纬度,起点经度","to":"终点纬度,终点经度"})。这里是参数格式说明，不是可直接提交的真实坐标。
6. 保存完整响应、调用时间、耗时，以及所选路线的距离和预计时间；若存在多条路线，明确选择哪条及选择规则。

本次 directionDriving schema 仅暴露 from、to。虽然描述提到偏好策略，不能擅自添加未暴露的 policy 等参数。

## 5. Key 申请与接入步骤（供复现）

1. 打开[腾讯位置服务快速注册入口](https://lbs.qq.com/dev/console/quick-register)，登录并按平台要求完成开发者注册。
2. 创建应用，可命名为 RoutePilot-Spike；创建自己的 Key，并开启 **WebServiceAPI**。这不是腾讯云 SecretId/SecretKey。
3. 给 Key 分配地址解析和驾车路线规划的调用额度；如果需要地点候选搜索，也检查对应权限和额度。不能仅凭创建成功就认定可调用。[官方入门指南](https://lbs.qq.com/service/webService/webServiceGuide/overview)明确要求申请 Key 后分配额度。
4. 将 Key 保存在本机私人配置文件中，并向本任务提供文件路径即可；不要写进本报告或 sources。本次 Key 仅用于进程内调用，没有保存到项目配置或证据文件。
5. 加载 Key，运行第 4 节链路。此次已完成；若未来遇认证、配额或校验限制，按实际错误排查，不预先修改账号安全设置。

如选择 WorkBuddy，可在其 MCP 配置界面新增远程 SSE 服务；界面具体名称以当前版本为准，本次未操作或验证其 UI。配置值为：

```text
名称：Tencent Location / RoutePilot Spike
类型：SSE
地址：https://mcp.map.qq.com/sse?key=<你申请的Key>&format=1
```

支持 mcpServers JSON 的客户端可参考以下配置模板（必须在客户端本地替换占位符，不是已生效配置）：

```json
{
  "mcpServers": {
    "tencent-location": {
      "url": "https://mcp.map.qq.com/sse?key=<YOUR_KEY>&format=1"
    }
  }
}
```

## 6. 问题、原因与修复记录

| 问题 | 证据/原因 | 处理及状态 |
| --- | --- | --- |
| uv 默认缓存不可写 | ~/.cache/uv/sdists-v9/.git 报 Operation not permitted | 将 UV_CACHE_DIR 指向 /private/tmp/routepilot-uv-cache；该错误已消除 |
| 依赖尝试源码构建失败 | cryptography 50.0.1 构建尝试安装 Rust，缓存路径不可写 | 改为仅安装二进制包，解析到兼容的 cryptography 48.0.1；SDK 安装、导入和实际调用成功 |
| 网页读取工具无法打开部分官方文档 | safe-to-open 错误或抓取超时，不能据此判断官网故障 | 通过本机 HTTPS 成功读取官方接入说明、WebService 入门及路线文档 |
| curl SSE 探测最终超时 | 20 秒前已收到 HTTP 200、endpoint、ping；SSE 是长连接 | 该截止超时不是连接失败；随后用 MCP SDK 完成握手和工具列表验证 |
| geocoder 返回 Invalid Key | 请求未提供 Key，用户确认尚未申请 | 已修复；用户提供 Key 后，两次 geocoder 和两次 directionDriving 均成功 |
| duration 单位容易误读 | 腾讯驾车规划文档明确为分钟 | 文档中明确单位转换；尚未实现应用接入代码 |

## 7. 数据约定与 V1 适配判断

[腾讯官方驾车路线文档](https://lbs.qq.com/service/webService/webServiceGuide/webServiceRoute)规定：distance 为米；duration 为结合路况的预计分钟数。因此 RoutePilot 如使用秒，应采用：

```text
distance_m = 腾讯路线 distance
duration_s = 腾讯路线 duration × 60
```

不能根据字段名 duration 推断所有接口都使用秒；其他接口须分别核对单位。保留腾讯原始值和单位，以便审计。驾车预计时间会受到路况影响，本次已获得查询当时的预计时间，但没有跨时段对照，无法量化路况影响，也未验证未来出发时间。

本次只验证两个地点；matrix、waypointOrder 等工具虽已发现，但没有执行，不能据此认定多点能力及账号权限通过。后续 V1 使用范围、额度和服务条款应以用户账号及官方当前说明为准，本次未对商业可用性作结论。

## 8. 有效 Key 重测结果与验收

### 8.1 原始地名链路

2026-09-11 北京时间 23:43:17 开始地点解析，23:44:01 开始包含驾车查询的测试会话。两次 geocoder 和 directionDriving 均返回业务 `status=0`，MCP `is_error=false`。

| 输入 | 实际解析名称 | 纬度 lat | 经度 lng | 调用耗时 |
| --- | --- | --- | --- | --- |
| 北京市朝阳区东坝 | 东坝家园A区-204号楼 | 39.968401 | 116.543148 | 80 ms |
| 北京市朝阳区国贸 | 国贸-11号楼 | 39.909557 | 116.456779 | 171 ms |

两者均返回朝阳区 adcode=110105。尽管 similarity=0.99，解析成具体楼栋仍说明语义存在歧义，不能将“接口成功”当作“符合用户地点意图”。

实际驾车输入：

```json
{"from":"39.968401,116.543148","to":"39.909557,116.456779"}
```

返回 1 条路线，采用 routes[0]：距离 **16444 米（16.444 公里）**，duration **25 分钟（1500 秒）**，13 个红绿灯，toll=0，调用耗时 432 ms。这只适用于上述两个解析楼栋，不作为抽象“东坝→国贸”的唯一答案。

### 8.2 明确 POI 的补充样例

为消除测试描述歧义，将补充样例明确为 **东坝地铁站 → 国贸地铁站**。这是本次技术测试选定的地标，不代表用户指定了个人实际出行地点或车辆入口。

先调用 placeSuggestion，keyword 分别为“东坝地铁站”“国贸地铁站”，region="北京"。耗时分别为 91 ms、188 ms。按精确站名、city="北京市"、adcode=110105 筛选，得到：

| 地点 | POI ID | 纬度 lat | 经度 lng |
| --- | --- | --- | --- |
| 东坝[地铁站] | 2199034917382 | 39.965717 | 116.547126 |
| 国贸[地铁站] | 10003443639928638601 | 39.908432 | 116.459729 |

发现：国贸候选中包含深圳市同名站，尽管请求指定 region="北京"。本次通过 city 和 adcode 排除，说明城市参数不能替代结果校验。该次响应 count=21、data 实际返回 10 条；本次仅筛选已返回候选，没有声称穷尽所有地点。

2026-09-11 北京时间 **23:44:37** 开始补充路线测试会话，实际输入：

```json
{"from":"39.965717,116.547126","to":"39.908432,116.459729"}
```

返回业务 status=0、MCP is_error=false，共 1 条路线，采用 routes[0]：

```json
{
  "origin": "东坝[地铁站]",
  "destination": "国贸[地铁站]",
  "distance_m": 15028,
  "duration_min": 18,
  "duration_s": 1080,
  "traffic_light_count": 8,
  "toll": 0,
  "tool_latency_ms": 454
}
```

以上为从真实响应提取并换算的摘要，不是原始响应字段集合。时间按官方文档的分钟单位解释，18×60=1080 秒。地铁站坐标是明确地标，但本次没有验证车辆可停靠的出入口。

两条驾车结果均返回 restriction.status=1。结合官方文档，该值表示途经包含限行的城市，不能认定已经按具体车牌避让限行；本次工具输入也未传车牌。此结果用于地图数据链路验证。

### 8.3 重测证据

- [有效 Key 的握手、工具定义和两次 geocoder 完整响应](spike-01-evidence/authenticated-geocoder.json)
- [原始楼栋间路线与两个地点候选完整响应](spike-01-evidence/authenticated-route-and-poi.json)
- [明确 POI 路线完整响应](spike-01-evidence/verified-poi-route.json)

证据包含原始路线折线和步骤，不包含 Key。记录的 tested_at 是各测试会话开始时刻，elapsed_ms 是各工具调用耗时；不是逐条请求的精确发出时刻，也不是性能统计。

### 8.4 验收结论

- [x] 官方 MCP 连接与工具发现成功。
- [x] 有效 Key 下两个地址解析成功。
- [x] 使用实际解析坐标取得真实驾车距离和时间。
- [x] 发现地名歧义并以明确 POI 补充验证。
- [x] 保存完整证据，核对米、分钟、秒的转换。
- [x] 更新 V1 数据源结论：最小技术能力通过，可用于后续 V1。

本次授权范围内的 Spike 已完成。矩阵接口、排序功能、规模化配额、长期稳定性、跨时段交通变化及商业使用条件未测试，仍不能据此宣称完整 V1 已验证。

## 9. 官方参考

- [MCP 能力概述](https://lbs.qq.com/service/MCPServer/MCPServerGuide/overview)
- [MCP 接入说明](https://lbs.qq.com/service/MCPServer/MCPServerGuide/userGuide)
- [WebService 入门与额度要求](https://lbs.qq.com/service/webService/webServiceGuide/overview)
- [驾车路线字段及单位](https://lbs.qq.com/service/webService/webServiceGuide/webServiceRoute)
- [开发者快速注册](https://lbs.qq.com/dev/console/quick-register)

参考文档核对日期：2026-09-11。文档说明、工具发现和业务成功调用在本报告中分别记录，不能互相替代。

## 10. 归档交接

归档日期：2026-09-12。测试执行日期保持为 2026-09-11；此次仅整理交付，未重新调用地图 API。

本报告与 docs/spike-01-evidence 下六份证据一起保存在 RoutePilot 所在的共享项目目录。独立归档包为 archives/routepilot-spike-01-2026-09-12.tar.gz；校验清单为 archives/routepilot-spike-01-2026-09-12-manifest.json。归档包保留 docs 相对目录，解压后报告中的证据链接仍然有效。

交接摘要：腾讯 MCP 的地点解析、候选搜索和两点驾车查询通过。明确 POI 样例为北京东坝地铁站→国贸地铁站，15028 米、18 分钟（1080 秒）。原始模糊地名解析到楼栋的样例为16444米、25分钟；两者不可混用。V1 需做城市过滤、地点消歧、分钟到秒转换，并保留路线限行信息。多点矩阵、路线优化、未来时间预测、H5 导航与商业可用性不属于本次通过范围；后续 Spike 的结论由各自文档负责。

Key 不纳入本归档。当前分支任务归档不删除文件，也不影响其他 RoutePilot 任务。
