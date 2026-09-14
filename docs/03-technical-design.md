# RoutePilot｜03 Technical Design v0.1

## 1. 技术设计目标
RoutePilot V1 需要完成：

> 用户自然语言输入 → 识别地点 → 地点标准化 → 获取真实路线成本 → 计算最优访问顺序 → 生成路线结果 → 地图展示 → 分享 → 拉起地图导航

核心原则：

> **LLM 负责理解，算法负责优化，地图服务负责真实世界数据。**

## 2. 系统总体架构
```text
                   用户
                    │
                    ▼
          RoutePilot Web / WorkBuddy
                    │
                    ▼
              Intent Parser
           自然语言结构化解析
                    │
                    ▼
              Location Resolver
           地点标准化 / 消歧
                    │
                    ▼
          腾讯位置服务 MCP
          Geocode / Search / Matrix
                    │
                    ▼
             Cost Matrix
       时间矩阵 / 距离矩阵
                    │
                    ▼
       Route Optimization Engine
              Python 算法
                    │
                    ▼
              Trip Result
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      H5地图页面           LLM解释层
          │                   │
          └─────────┬─────────┘
                    ▼
               Trip Page
                    │
           ┌────────┴────────┐
           ▼                 ▼
        微信分享          地图App导航
```

## 3. WorkBuddy 的角色
### Role A：Agent Runtime
负责：
- 理解用户请求
- 触发 RoutePilot Skill / Agent
- 调用腾讯位置服务 MCP
- 调用路线优化程序
- 返回结果

### Role B：Prototype UI
正式 Web 产品之前，WorkBuddy 可作为第一版交互入口。

## 4. V1 是否需要 Agent
需要轻量 Agent，但不需要高度自主 Agent。

V1 更合理的是：

> **Agent + Deterministic Workflow**

### Agent 负责
- Intent Understanding
- Missing Information
- Ambiguity Handling
- Result Explanation

### Workflow 负责
```text
Input Validation
      ↓
Geocoding
      ↓
Location Confirmation
      ↓
Distance Matrix
      ↓
Optimization
      ↓
Route Detail Query
      ↓
Generate Result
      ↓
Save Trip
```

## 5. 腾讯位置服务 MCP 的职责
至少需要：
- Geocoding
- POI Search
- Distance Matrix
- Route

未来可扩展：
- Traffic
- Along Route POI
- Gas Station
- Parking

## 6. Cost Matrix
需要 Time Cost Matrix 和 Distance Cost Matrix。

A→B 与 B→A 不一定相等。

路线优化算法本质上是在矩阵中寻找总代价最小的路径。

## 7. 路线优化算法
V1 只有 3–8 个目的地，因此优先使用：

> **Brute Force / Exhaustive Search**

原因：
- 实现简单
- 结果一定最优
- 易 Debug
- 易验证

6 个途经点：6! = 720
8 个途经点：8! = 40,320

如果未来扩展到 20 / 50 / 100 个地点，再考虑：
- OR-Tools
- Heuristic
- Genetic Algorithm
- Simulated Annealing
- VRP Solver

## 8. 固定起点和终点
例如：
```text
Start = 杭州
Waypoints = 南浔 / 乌镇 / 西塘
End = 上海
```

只对 waypoints 做排列。

## 9. fastest vs shortest
### Fastest
优化目标：
```text
MIN total_travel_time
```

### Shortest
优化目标：
```text
MIN total_distance
```

默认：**Fastest**。

## 10. Route Optimization Engine
建议使用 Python。

核心函数：
```text
optimize_route(
    start,
    waypoints,
    end,
    cost_matrix,
    objective
)
```

输出：
```json
{
  "optimized_order": [
    "杭州",
    "南浔",
    "乌镇",
    "西塘",
    "上海"
  ],
  "total_duration": 15600,
  "total_distance": 228000
}
```

约定：
- `total_duration`：秒
- `total_distance`：米

## 11. 为什么不让 LLM 排路线
LLM 可以解释，但不能证明最优。

RoutePilot 的可信度来自：

> **Real Map Data + Deterministic Algorithm**

## 12. Trip 数据模型
```json
{
  "trip_id": "RT202609110001",
  "created_at": "...",
  "start": {},
  "waypoints": [],
  "end": {},
  "original_order": [],
  "optimized_order": [],
  "objective": "fastest",
  "total_duration": 15600,
  "total_distance": 228000,
  "segments": []
}
```

Trip 需要保存，因为后续分享、H5、导航、Eval、Debug 都依赖它。

## 13. Database：SQLite
V1 使用 SQLite。

原因：
- 不需要独立数据库服务
- 适合本地开发 / Demo / PoC
- Python 原生支持
- 未来可迁移 PostgreSQL / MySQL

## 14. Backend：Python + FastAPI
FastAPI 用于把 Python 能力开放为 HTTP API。

示例接口：
```text
POST /trips
GET /trips/{id}
POST /trips/{id}/optimize
GET /trips/{id}/share
```

## 15. Frontend
V1 使用：

> **HTML + CSS + Vanilla JavaScript**

不使用 React / Vue，优先简单、快速、易调试。

## 16. 地图展示
使用：

> **腾讯地图 JavaScript SDK**

负责：
- Marker
- Polyline
- Info Window
- 视野范围
- 地点名称

地图 API 提供数据；JS SDK 负责可视化。

## 17. 分享链接
示例：
```text
routepilot.com/t/abc123
```

本质是分享一个 Trip ID。

## 18. Navigation / Deep Link Adapter
定义统一接口：

```text
open_navigation(provider, trip)
```

内部实现：
- TencentMapAdapter
- BaiduMapAdapter
- AmapAdapter

目的：隔离不同地图厂商 URI/Deep Link 差异。

### Preferred Path
目标地图 App 支持完整多途经点时，一次性交付整条路线。

### Fallback Path
不支持完整多途经点时，由 RoutePilot H5 保留完整 itinerary，并按段唤起导航。

## 19. Logging / Observability
至少记录：
```text
request_id
trip_id
user_input
parsed_locations
geocode_result
matrix_latency
optimization_latency
chosen_route
map_api_errors
navigation_click
share_click
```

## 20. Error Handling
- MCP / API 超时：Retry 1–2 次
- Geocode 失败：停止优化
- Matrix 缺路段：不得让 LLM 猜
- Optimization 失败：保留原始顺序并明确报错

## 21. V1 技术栈
| 层 | 方案 |
|---|---|
| LLM / Agent | WorkBuddy |
| Skill | RoutePilot Skill |
| Maps Connector | 腾讯位置服务 MCP |
| Backend | Python + FastAPI |
| Algorithm | Python Exhaustive Search |
| Database | SQLite |
| Frontend | HTML + CSS + JavaScript |
| Map Visualization | 腾讯地图 JS SDK |
| Share | H5 URL + Trip ID |
| Navigation | Deep Link Adapter |
| Version Control | GitHub |

## 22. Repository 结构建议
```text
routepilot/
├── README.md
├── docs/
├── app/
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── optimization/
│   ├── models/
│   └── database/
├── web/
├── tests/
└── skills/
    └── routepilot/
```

## 23. 核心技术风险
- R1：腾讯 MCP Matrix 是否满足 3–8 点需求
- R2：路线 Cost 是否受实时交通影响导致结果不稳定
- R3：腾讯地图 Deep Link 多途经点支持情况
- R4：微信内 H5 → 地图 App 的唤起限制
- R5：地点自然语言解析 / 消歧准确率

## 24. Technical Spike 顺序
- Spike 01：腾讯位置服务 MCP 跑通
- Spike 02：多点 Distance Matrix
- Spike 03：路线优化算法
- Spike 04：H5 / 微信 / 地图 App Deep Link
