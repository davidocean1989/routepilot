# RoutePilot｜02 PRD v0.1

## 1. 产品目标
RoutePilot V1 聚焦一个单一问题：

> **旅行用户一天内想去 3–8 个地点时，帮助其自动计算更合理的访问顺序，并把结果变成可查看、可分享、可直接导航的完整旅行路线。**

V1 成功意味着用户可以完整完成：

**输入地点 → 得到优化路线 → 看地图 → 分享给同行人 → 开始导航。**

## 2. V1 核心场景
用户说：

> “我明天从杭州西湖出发，想去南浔古镇、乌镇、西塘古镇，晚上住上海静安寺，怎么走最顺？”

RoutePilot 应完成：
1. 理解起点、目的地、终点；
2. 确认地点无歧义；
3. 获取真实道路距离 / 时间；
4. 计算最合理访问顺序；
5. 给出总里程和总驾驶时间；
6. 和用户输入顺序进行对比；
7. 生成完整路线地图；
8. 生成微信可分享链接；
9. 支持进入地图 App 导航。

## 3. V1 用户输入
第一入口是一句话输入，而不是复杂表单。

如果用户没有明确终点，系统可默认最后一个地点为终点，必要时询问是否需要回到起点。

UX 原则：

> **能少填一个字段，就少填一个字段。**

## 4. F01｜自然语言地点解析
### 输入
一段自然语言。

### 输出
结构化：
- 起点
- 目的地列表
- 终点
- 交通模式（V1 默认驾车）

### Acceptance Criteria
- 能解析 3–8 个地点；
- 保留用户原始输入顺序；
- 无法确定地点时必须追问；
- 不允许偷偷替换用户地点。

## 5. F02｜地点标准化与消歧
调用腾讯位置服务 POI Search / Geocoding。

每个地点保存：
```text
name
address
lat
lng
poi_id（如有）
```

### Acceptance Criteria
- 所有进入路线算法的地点必须有标准坐标；
- 搜不到或存在多个高概率结果时不得继续计算；
- 必须结合城市 / 行政区做筛选与消歧。

## 6. F03｜距离 / 时间矩阵
需要获得所有点之间的：
- Distance Cost
- Time Cost

注意：A→B 与 B→A 不一定相等。

V1 默认优化目标：**最快路线**。

## 7. F04｜路线优化 Engine
输入：
- 起点
- 目的地集合
- 终点
- Cost Matrix
- Optimization Objective

输出：
- 推荐访问顺序
- total_duration
- total_distance
- 相比原始顺序节省的时间 / 距离

V1 支持：
- fastest
- shortest

## 8. F05｜结果页
第一屏只展示：
1. 推荐顺序
2. 总里程 / 总时间
3. 优化收益
4. 两个按钮：查看地图 / 开始导航

## 9. F06｜分段路线明细
显示每一段：
- 起点 → 终点
- 距离
- 预计时间

## 10. F07｜RoutePilot 地图页面
地图至少显示：
- 起点
- 途经点
- 终点
- 顺序编号
- 完整路线
- 每个点名称

RoutePilot 必须保存完整 itinerary，作为 Source of Truth。

## 11. F08｜Trip 分享链接
每次路线计算完成后创建 `trip_id`。

分享链接示例：

```text
routepilot.app/t/8F2KX
```

V1 不要求登录。

## 12. F09｜微信传播
要求：
- RoutePilot 分享页可在微信内正常打开；
- 微信链接先打开 RoutePilot H5，再从 H5 选择导航。

## 13. F10｜地图 App 导航
### Preferred Path
如果地图 App 支持完整多途经点，则整条路线一次性交给地图 App。

### Fallback Path
如果不支持，则 RoutePilot H5 保留整个 itinerary，并按段唤起导航。

### 地图兼容优先级
- P0：腾讯地图
- P1：百度地图
- P2：高德地图

## 14. V1 页面结构
### Page 1｜输入页
自然语言输入框 + “帮我排路线”。

### Page 2｜地点确认
展示起点、途经点、终点，支持删除/修改/调整。

### Page 3｜结果 / 地图页
展示：
- 推荐路线
- 指标
- 优化收益
- 地图
- 分段明细
- 分享
- 导航

## 15. 异常状态
- E01 地点找不到
- E02 地点有歧义
- E03 路线不可达
- E04 地图 API 调用失败
- E05 地点过多
- E06 地图 App 无法唤起

## 16. 非功能需求
### Performance
正常 3–8 点路线：
- 目标：10 秒内
- 上限：60 秒内返回

### Reliability
外部地图 API 失败需要 Retry / Error Handling。

### Security
地图 API Key 不暴露给前端。

### Observability
至少记录：
- request_id
- trip_id
- user_input
- parsed_locations
- geocode_result
- matrix_latency
- optimization_latency
- chosen_route
- map_api_errors
- navigation_click
- share_click

## 17. V1 Evaluation
### Level 1｜功能正确
- 地点解析成功率
- Geocoding 成功率
- Route Matrix 成功率
- 路线生成成功率

### Level 2｜算法价值
- 平均节省里程
- 平均节省时间
- 有改善的 Case 比例

### Level 3｜用户价值
- 是否采用推荐路线
- 是否分享
- 是否点击导航
- 下次是否愿意继续使用

## 18. North Star Metric
**Successful Optimized Trip**

定义：一次用户请求满足：
1. 成功识别全部地点；
2. 成功生成优化路线；
3. 用户打开结果；
4. 用户点击“开始导航”或“分享”。

## 19. V1 暂不做
- 景点推荐
- AI 自动增加景点
- 景点介绍
- 门票
- 酒店
- 餐厅推荐
- 天气
- 加油
- 充电
- 时间窗
- 停留时长
- 公交/高铁组合
- 实时动态重新排序
