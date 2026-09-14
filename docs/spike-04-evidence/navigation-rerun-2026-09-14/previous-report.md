# 07｜Technical Spike 04：H5 / 微信 / 地图 App Deep Link

项目：Davidocean · AI Career / RoutePilot  
对外名：**一趟跑完**；副标题：**一天跑 6 个地方，怎么走最顺？**  
日期：2026-09-12（Asia/Shanghai）  
状态：**已结项归档。用户确认高德完整5站路线严格保持顺序且能进入导航；最终结论见第14节，之前各节保留为实验历史。**

> 编号说明：原 `technical-spike-04.md` 是“预定时间与停留时间”实验，完整保留在 [原报告](technical-spike-04-scheduled-time.md)，其 `spike-04-evidence/` 未改动。本报告对应用户要求的文档序号 07 / 导航 Spike 04。既有导航记录见 [technical-spike-06.md](technical-spike-06.md)，本轮不修改那份历史报告。

## 1. 决策

**最终V1建议：高德优先提供完整路线交付（本例已由用户确认顺序及导航启动），腾讯/百度以逐段直达App备用；RoutePilot始终保留完整itinerary。容量上限及其他版本/平台仍未知，保留逐段回落。需要调整PRD的交付承诺。**

三家地图不能简单合并成“支持/不支持多点”一个布尔值。网页接口、App URI、导航 SDK、服务端算路接口是不同产品；后两者的途经点上限不能用于证明 H5 调起现成 App 的能力。多点路线接收也不等于启动导航，更不等于保留 RoutePilot 算出的道路路径或 ETA。

本轮没有连接 iPhone、Android 或手机微信。不能把桌面浏览器、User-Agent 判断、参数生成、页面进入后台当作真机成功。所有新协议入口仍需真机复验。

## 2. 原型与固定行程

原型文件：[spike04.html](../routepilot-nav-test/dist/spike04.html)、[页面逻辑](../routepilot-nav-test/dist/spike04.js)、[三个 Adapter](../routepilot-nav-test/dist/navigation04.js)。沿用现有静态页面结构，新增独立入口，不改旧腾讯测试页。无后端、无登录实现、无优化计算、无行程编辑、无自动发送记录。

- 固定行程 `rp-spike04-demo-v1`，revision=1，GCJ-02。
- 顺序：杭州东站 → 乌镇西栅景区1号停车场入口 → 南浔古镇1号停车场入口 → 西塘古镇景区第一地上停车场 → 上海虹桥站。
- 5 个总点 = 2 个端点 + 3 个途经点 = 4 段。品牌副标题中的“6 个地方”不是本次样本数。
- 坐标沿用现有导航测试页和 Spike 02；固定顺序用于比对，不声称最快、最短或代表实际出行计划。
- 页面展示完整有序地点、坐标、行程编号、地图选择、系统选择、当前段、“开始导航”、网页地图、完整路线实验、复制目的地、分享链接与本机结果记录。
- 原型保留现有客户端腾讯 Key 用法，新增页复用同一已配置 Key；不另行获取或开通服务。发布包不得包含服务端凭证、历史调用响应或手机记录。

分享形式：`/spike04.html?trip_id=rp-spike04-demo-v1&segment=2`，segment 从0计数，即第3段。切换段时更新 URL；复制的是 RoutePilot 行程链接，**不是地图 App 链接**。trip_id 不发送给地图服务。未知或重复 trip_id、非法路段显示错误，不冒充另一个行程。缺省参数进入固定演示行程。

## 3. 官方协议对照

核对日期为本报告日期；“未列出”只指本次查阅接口，不是断言该品牌任何产品都不支持。

| 地图/入口 | 协议与关键参数 | 多途经点与上限 | 本轮结论 |
|---|---|---|---|
| 腾讯 Web | `https://apis.map.qq.com/uri/v1/routeplan`；fromcoord/tocoord，纬度在前，coord_type=2 | 历史官方核对未列出途经点；上限未知 | 用于单段网页兜底 |
| 腾讯 App，iOS/Android | `qqmap://map/routeplan`；type=drive，from/fromcoord，to/tocoord，referer=客户端 Key | 历史核对未确认多途经点；不生成猜测参数 | 单段；iPhone Safari 历史路线接收通过 |
| 高德 Web | `https://uri.amap.com/navigation`；from/to 为经度,纬度,名称；via；mode=car；callnative | **via 最多1个**，仅驾车 | 无法通过该接口交付本例3个途经点 |
| 高德 Android App | `amapuri://route/plan/`；slat/slon、dlat/dlon、t=0、dev=0，sourceApplication | vian、vialons、vialats、vianames；列表用竖线分隔；**文档未给数值上限** | 有多点参数；可生成完整路线实验链接，未确认实际接收 |
| 高德 iOS App | `iosamap://path`；起终点和多点字段同上 | **文档未给数值上限** | 同上；不是网页 via 的1点限制 |
| 百度 Android App/H5 | 原生示例 `baidumap://map/direction`；H5示例 `bdapp://map/direction`；origin/destination、mode=driving、coord_type=gcj02、src | direction 文档列出 viaPoints JSON；navi 章节给出嵌套 viaPoints 数组结构；**未列数值上限** | H5 使用 bdapp；完整链接是候选，direction 对该结构的实际接收待验证 |
| 百度 iOS App/H5 | direction 示例 `baidumap://map/direction`；纬度在前，coord_type=gcj02 | 本次 iOS 页未列 viaPoints；**未知** | 单段；不把 Android 字段视为 iOS 保证 |
| 百度 Web | `https://api.map.baidu.com/direction`；origin/destination、coord_type=gcj02、mode=driving、output=html、src | 本次 Web 参数表未确认完整多点传递 | 单段网页入口候选；HTTPS 链接实际移动端表现待测 |

依据：[高德 Web](https://lbs.amap.com/api/uri-api/guide/travel/route)、[高德 Android](https://lbs.amap.com/api/amap-mobile/guide/android/route)、[高德 iOS](https://lbs.amap.com/api/amap-mobile/guide/ios/route)、[百度 Android](https://lbsyun.baidu.com/docs/webapi?title=mapadjustment/uri/andriod)、[百度 iOS](https://lbsyun.baidu.com/docs/webapi?title=mapadjustment/uri/ios)、[百度 Web](https://lbsyun.baidu.com/docs/webapi?title=mapadjustment/uri/web)。腾讯来源为[Web URI](https://lbs.qq.com/uri_v1/guide-route.html)和[App URI](https://lbs.qq.com/uri_v1/guide-mobile-navAndRoute.html)，**本轮抓取失败，参数证据继承历史报告，不能称本轮成功复核了腾讯最新文档**。

高德 App 官方页面更新时间2025-10-15，Web页2025-03-03。App 页面所述基础支持版本并不证明多点字段从同一旧版本起就可用。高德 m 偏好参数在较新 Android/iOS 版本已不支持，以 App 本地偏好为准；原型传 m=0 是兼容字段，不能保证“最快”接管。百度 iOS 文档明确真实导航以当前位置为起点；固定远端起点的路线展示与从该起点启动导航应分别验收。

### Universal Link / Android App Links

三家本轮均**未找到并验证可交付任意完整多点路线的官方 Universal Link 合约**。不能把 HTTPS 网页入口、网页内脚本尝试唤起、或官方 App 自带分享短链统一称为 Universal Link 已通过。本轮也未验证三家 App 的域名关联文件及允许的路径范围。

Apple 要求站点关联文件与 App 的关联域名配置配套；RoutePilot 无法仅给自己的域名添加一个文件就让第三方地图接管任意链接。Android App Links 同样需要 App 与域名的可验证关联。来源：[Apple Universal Links](https://developer.apple.com/library/archive/documentation/General/Conceptual/AppSearch/UniversalLinks.html)、[Android Deep Links](https://developer.android.com/training/app-links)。

V1 优先使用有文档的 URI，Universal Link 能力字段保持 unknown。未来如地图厂商提供明确路线合约，再验证安装/未安装、微信/外部浏览器、参数顺序、域名关联和回落网页。不要通过猜测私有链接或从 SDK 接口推导 Universal Link。

## 4. 平台与微信策略

| 场景 | 可用证据 | V1 行为 |
|---|---|---|
| iPhone Safari + 腾讯已安装 | 历史用户反馈可唤起并带入路线；版本和四段逐项核验缺失 | 候选首选组合，仍要求核对地点并在 App 确认导航 |
| 同一 iPhone 微信 + 腾讯 | 历史反馈：网页路线可看，直接 App 唤起无反应 | 保留行程；提示“…”在浏览器打开，或复制行程链接到 Safari |
| Android 微信/外部浏览器 + 腾讯 | 未测 | 不显示“已兼容”；提供同样 fallback |
| iOS/Android + 百度/高德 | 本轮仅协议与参数验证 | 实验候选，按平台逐项验收 |
| 未安装 App | 未测，Scheme 本身没有可保证的网页回落 | 显式“网页地图”“复制目的地”，不定时强跳应用商店 |
| 系统提示被取消、微信无响应 | 不能可靠区分取消、拦截、未安装 | 显示未确认与可操作回落，不宣称未安装 |

高德 Web 官方文档明确指出部分微信/QQ内置浏览器无法成功通过 callnative 调起；这不是所有微信版本、所有地图、所有机制的统一结论。腾讯微信失败有项目历史反馈支撑，具体拦截原因未证实。

按钮用用户直接点击的原生链接，不在页面加载时唤起，也不在等待网络请求后唤起。2200ms仅用于显示帮助；visibilitychange 仅记录离开前台/返回，不自动写入成功、到达或切换下一段。无可靠完成回调时，由用户确认下一段。

微信 JS-SDK/openLocation、开放标签等另有平台接入条件，不能视作对三家任意 App 的通用突破口。本轮未接公众号签名服务、未核验资格，不作为 V1 的必需路径，也不声称其不可用。

## 5. Preferred Path 与 Fallback Path

**Preferred：整条路线一次性交付。** Adapter 检查平台/版本已验收、途经点数量不超已确认容量、有序传输能力与用户选择；构造 start + ordered waypoints + end；用户点击；在 App 中核对全部点数量、名称/位置和顺序；再确认导航。原型的高德双平台、百度 Android 完整路线入口只用于实验，productionEnabled=false。

成功必须满足：没有静默截断/重排；起终点正确；进入驾车路线；能够继续导航；返回 H5 后原 itinerary 仍在。只接收目的地或只打开 App 判失败。App 重新算道路和 ETA 可以接受，但不得宣称延续原优化时间或道路折线。无法确认容量时不在生产自动走 Preferred，更不能“尽量塞进去”后忽略遗漏站点。

**Fallback：逐段交付。** H5 始终是完整行程的权威来源；显示当前第k段、上一站与下一站 → 用户启动地图 → 返回 H5 → 用户核对并选下一段。失败时依次提供外部浏览器打开当前行程、网页路线、复制目的地。完整路线实验失败不自动换成“起点直达最终终点”。

本原型固定起点是为了对照；产品真正出发时应区分“预览计划路段”和“从当前位置去下一站”，后者仍保留下一站及全局访问顺序。偏离原起点时不把规划起点当实时位置。跨浏览器 localStorage 不共享，本原型靠分享 URL 恢复 trip_id/segment；生产应靠只读行程快照与版本恢复完整 itinerary，进度是否同步需在 PRD 单独定义。

## 6. NavigationAdapter 接口草案

```ts
type Environment = {
  os: 'ios' | 'android'; browser: 'wechat' | 'external';
  osVersion?: string; browserVersion?: string; mapVersion?: string;
};
type Trip = {
  trip_id: string; revision: number; coordinateSystem: 'gcj02';
  points: Array<{ name: string; lat: number; lng: number }>;
};
type Capability = {
  fullRoute: 'verified' | 'documented-unverified' | 'unknown';
  maxWaypoints: number | null; // null不是0，也不是无限
  orderVerified: boolean; universalLinkVerified: boolean;
};
type NavigationHandoff = {
  appUrl: string | null; webUrl?: string | null;
  pointCount?: number; reason?: string;
  productionEnabled: boolean; navigationConfirmed?: false;
};
interface NavigationAdapter {
  capabilities(): Capability;
  buildSegment(trip: Trip, index: number): NavigationHandoff;
  buildFullRoute(trip: Trip): NavigationHandoff;
}
// TencentMapAdapter(os, clientKey)
// BaiduMapAdapter(os)
// AmapAdapter(os)
// 页面层：保存分享 URL、直接点击、诊断、回落及用户反馈。
```

本轮实现是无网络的协议构造器。生产草案需把 capability 按地图版本/OS/浏览器及验收证据索引，并加上数量和坐标校验、名单策略、来源/版本标识、结构化失败码。不得把实验阶段 `buildFullRoute` 直接接到生产主按钮。现有原型仅支持固定演示数据，不接受任意用户点集。

坐标不做无依据二次偏移：腾讯 GCJ-02；高德 dev=0；百度显式 gcj02。高德 Web 经度在前，腾讯和百度的组合坐标纬度在前。中文及 JSON 只编码一次，百度不要把已编码 JSON 再交给 URLSearchParams。不同地图 POI ID 不互传，停车入口需逐点验收。

## 7. 验证结果与证据分级

| 项目 | 结果 | 证据与边界 |
|---|---|---|
| 固定路线、三个 Adapter、链接生成 | 通过本地测试 | [测试脚本](../routepilot-nav-test/tests/navigation04.cjs)：24组单段交接（48个 App/Web 链接），OS协议、坐标字段、多点顺序与降级分支 |
| 完整路线 payload | 参数验证通过 | 高德3个有序途经点；百度 Android JSON数组；不证明 App 收到 |
| trip_id/segment 解析、未知ID | 本地测试通过 | 保留ID/段号；拒绝未知、重复ID和非法段号 |
| 桌面浏览器初始渲染 | 通过首次观察 | 实际页面显示rp-spike04-demo-v1与第3段南浔→西塘，分享框参数一致 |
| 桌面后续点击/切换与手机视觉 | 未完成 | 后续自动交互报告浏览器会话不匹配；未把测试工具故障当页面故障 |
| 微信打开分享并保留trip_id | **未测** | 历史页不含此新参数，历史“页面可开”不能覆盖新要求 |
| 三家双平台实际启动导航 | **未测** | 无连接手机，历史腾讯Safari仅确认路线接收 |
| 整条路线容量与顺序 | **未测** | 尚无3–8个途经点实机输入/接收对照 |
| 微信公共分享入口 | 新版已公开发布，微信待测 | Sites v2 已发布、权限 public；自动匿名请求返回 Cloudflare 403，尚未确认手机访问 |

本地服务器首次受沙箱限制，获准后可启动；浏览器确实载入新版页面。参数测试和语法检查不能替代点击流程、手机微信或第三方地图测试。

### 容量实测方法

按“途经点数”统计，不把起终点算入。每个平台分别测试0、1、2、3、5、8个不同可达点。先用本原型3个途经点验证基础链路，再在独立fixture中添加真实入口POI（不可重复同一坐标冒充更多途经点）。若8个全通过，只能写“已验证至少8个”，不能写最大值8。继续测试9/16/17仅用于找到边界；发现截断/拒绝后以边界相邻数量复测两次。最终记录“文档上限”“本版本实测下界”“首次失败数量与表现”，不能推断所有版本上限。

顺序对照至少两组：乌镇→南浔→西塘，以及南浔→乌镇→西塘。逐一核对App列表与POI位置，检查是否默认重新优化；记录输入数量、接收数量、输出序列、导航启动状态、起点改写及返回结果。重复坐标或只查看地图折线不足以证明顺序。

## 8. 手机验收清单

[可填写矩阵](spike-04-navigation-evidence/device-matrix.csv)覆盖3地图×2系统×2浏览器×已安装/未安装，共24组合；本轮初值均为未测，历史反馈单独保留，不能自动计为本次版本通过。

1. 使用无需登录的新版HTTPS入口，把带trip_id与segment=2的完整链接手动粘贴到微信聊天/文件传输助手；本代理未发送任何消息。
2. 微信打开，核对行程编号、版本、5站顺序与第3段；刷新、再次打开、复制后在系统浏览器打开，参数和段号必须一致。记录重定向、登录、域名风险提示、空白页。
3. 选择地图与实际系统，点击当前段；分别记录系统弹窗、是否打开App、起终点、路线规划、实际导航。安装/未安装必须分别测，不凭超时推断。
4. 高德双平台/百度Android再打开整条路线实验，核对3个途经点；随后按容量方法补测。腾讯/百度iOS无确认参数时保持逐段，不填猜测字段。
5. 返回H5，确认行程仍在、未自动标为到达；手动选择下一段，直到4段都核对完。实际导航启动只在安全静止状态确认，不要求驾车。
6. 保存每次记录，填设备、系统、微信/浏览器和地图版本、是否安装、实际路线及截图证据位置；自行复制报告回任务。网页不自动上传记录。

## 9. 限制与用户体验问题

- 登录墙会打断微信传播；HTTPS 200也可能只是登录页。必须从未登录手机验证实际内容及参数。
- 微信→浏览器→App增加步骤；回到H5需要用户主动切换。文案必须解释接下来去哪，不要求理解URI或Key。
- 页面不能可靠探测App安装或导航成功；定时器仅提示，不能自动跳应用商店或记完成。
- 分享链接跨浏览器可恢复固定行程/当前段；测试记录在原浏览器，换浏览器不自动同步。
- App可能按实时定位、路况、个人避让偏好重新规划；不保证原路线距离/耗时，也不保证不同地图同名POI入口一致。
- URL长度、旧版App参数忽略、中文/JSON编码、坐标系、经纬度顺序、重复点、超容量静默丢弃均需实测。
- 原型只有一个公开地标行程，不能证明生产的权限、过期链接、快照持久化、分享卡片或微信朋友圈定制文案已完成。
- 微信 JS-SDK签名、公众号资格、Universal Link专用接入及App自动返回均未实现；不扩展到完整MVP。

## 10. V1 兼容策略与 PRD 调整建议

1. **主路径为逐段导航**，保留整条有序行程；腾讯作为已有iPhone Safari历史证据的优先候选，不能据此承诺Android已支持。提供地图选择，百度/高德未验收组合标实验。
2. 微信默认展示“在地图中打开”及浏览器打开帮助；网页路线/复制目的地始终可见。禁止承诺“微信内一键唤起所有地图”。
3. 高德iOS/Android、百度Android的Preferred Path先用实验入口收集容量与顺序证据；通过版本组合才进入启用名单。腾讯、百度iOS维持unknown，不一概标为品牌不支持。
4. PRD将“开始导航”定义为“交付路线并引导用户在第三方App确认”，将“打开App”“路线接收正确”“开始导航”分开衡量。按钮点击率不能作为导航成功率。
5. PRD明确完整路线交付是条件能力，V1不保证一次接管全部3–8途经点。规划端支持8个点/途经点的定义需统一，导航容量另算。
6. PRD新增可匿名访问的HTTPS行程快照、trip_id与revision保留、未知/过期行程错误、复制链接和跨浏览器恢复、人工进度选择。若生产行程涉及私人地址，公开与权限边界另行设计；本次仅公开地标fixture。
7. 在验收标准中加入24组合矩阵、实际点数与顺序、误位、静默截断、未安装、微信无响应、返回行程恢复；指标分母为已实际测试的组合/尝试。

**结论：架构上可继续，完整执行链路验收尚未通过。** 现有证据足以采用“RoutePilot负责行程顺序，地图负责当前段导航”的V1设计；不足以宣称三地图双平台微信内全兼容，或宣布任一家完整多点路线的实测最大容量。下一步应完成公开新版入口和真机矩阵，不扩展MVP开发。


## 11. 本轮交付与发布状态

新增页已完成本地检查，可通过本机静态服务器访问 `spike04.html?trip_id=rp-spike04-demo-v1&segment=2`。

自动审批拒绝向现有 Sites 项目主分支推送，理由为可能更新线上部署且未明确授权发布。本轮没有成功推送、保存新版或部署，现有线上地址仍是旧版；也没有修改站点的 owner-only 访问权限。需用户明确授权发布后再继续，不能把旧公开域名当作本次新版入口。

[可移植原型包](../artifacts/routepilot-spike04-prototype.zip)只含固定页面与测试，不含服务端凭证或历史API响应；保留现有前端腾讯客户端Key。要满足微信分享验收，发布目标还必须允许未登录访问。当前私有 Sites 发布即使成功，也不等于匿名微信分享通过。


## 12. 用户授权后的公开发布（2026-09-12）

用户明确授权将新版原型发布到现有 Sites 并开放免登录访问。此前审批阻塞已解除，推送成功，Sites v2 部署状态 succeeded，访问配置复核为 public。本节取代第11节关于“尚未发布/owner-only”的当前状态描述，原记录保留为历史。

- [站点首页](https://routepilot-navigation-lab.season1016.chatgpt.site)
- [新版原型与分享验证入口](https://routepilot-navigation-lab.season1016.chatgpt.site/spike04.html?trip_id=rp-spike04-demo-v1&segment=2)
- 发布提交：`5b9d5989957bd4373f78219169222be04e5db26a`
- 部署：`appgdep_6aa513429a288191a75338df79ca1a48`
- 新版文件与本地已验证原型一致；24组参数测试重新通过。旧首页保留，新版从 spike04.html 进入。

匿名HTTP检查：Python本机证书链校验失败；使用系统curl正常验证证书后，收到Cloudflare HTTP 403，响应含server: cloudflare与__cf_bm。未绕过安全校验或挑战。此结果不能证明仍有登录墙，也不能证明免登录手机访问已通过。Sites权限已公开，但微信/Safari/Android浏览器实际打开、trip_id保留与App接收继续待真机测试。


## 13. 首轮用户手机反馈与第二轮原型调整（2026-09-12）

证据来自本任务用户反馈及附件，非代理亲自操作手机。用户描述为“从微信里跳到内置浏览器之后”；具体浏览器、iOS和地图版本未提供，不能标为微信WebView直接唤起成功，也不擅自归类为Safari。截图有iPhone式系统界面，但系统版本仍未知。未确认这次每段均核验，也未明确确认trip_id和segment读数。

| 地图 | 本页单段直达 App | 网页及其二次跳转 | 完整行程 |
|---|---|---|---|
| 高德 | App打开且起终点带入 | 网页显示路线；网页内打开App也带入起终点 | App打开且全部途经点信息完整。当前固定样本为3个途经点；顺序逐项及实际导航启动仍需单独确认 |
| 腾讯 | App打开且起终点带入 | 网页路线可看；网页内开始导航跳小程序或App时丢失起终点 | 本原型未生成多点协议，没有按钮是预期行为 |
| 百度 | App打开且起终点带入；用户后续明确纠正为百度App，最初“腾讯”是反馈中的误写 | 附件显示百度“周边/生活服务”页面，而非指定路线，判路线展示失败 | iOS文档未确认多点参数，未生成按钮是预期行为 |

诊断：页面按所选provider构造不同scheme，新增运行测试验证高德→腾讯→百度→高德切换的按钮协议和名称，不存在已复现的跨地图协议串用。百度官方Web文档核对显示既有origin/destination、coord_type=gcj02、mode=driving、output=html、src符合参数表；该表允许坐标+名称，并未要求本次必须追加城市。截图不能展示完整重定向链，所以尚不能判定参数在哪一步被忽略，也不能宣称已修好百度网页。来源：[百度Web路线文档](https://lbsyun.baidu.com/docs/webapi?title=mapadjustment/uri/web)。

第二轮改动（页面标记“第二轮”，脚本spike04-v2）：

- 默认选高德，三家的直达App协议均保留，按钮明确显示地图名称。
- 高德完整行程入口直接展开，标注本例3个途经点已反馈完整带入；仍不启用生产兼容白名单、不猜最大数量。
- 腾讯网页仅推荐查看，明确提示网页内二次跳转丢参数，使用本页直达按钮进入App。
- 百度网页收进“故障复测（非推荐入口）”，保留同一链接便于复现，优先直达百度App/复制目的地。没有用未经文档支持的链接替换并冒充修复。
- 不支持完整交付的平台公开显示原因，而非仅隐藏按钮；保留百度Android实验能力，未承诺iOS完整路线。
- 分享链接增加provider，切换地图后复制/重开保留所选地图；无provider默认高德，未知或重复provider拒绝。保留trip_id、segment。
- 测试记录增加单条build版本，原本机记录保留，不把旧记录写成新版本验证。

最新V1建议：**高德优先、腾讯/百度逐段备用**。高德Preferred Path已从“只有文档与构造验证”推进到“当前样本完整地点接收的用户实测证据”，但尚需逐点顺序、导航启动、设备版本及至少8途经点样本才能定正式范围。三家单段App接收可记为本次测试环境通过；任何品牌的全平台、微信内直接调起、Universal Link和最大容量均未因此通过。

下一轮只需补测：高德完整路线顺序是否严格为杭州→乌镇→南浔→西塘→上海，并能进入导航；百度直达是否继续可用；腾讯直接按钮是否继续保留起终点。若复测百度网页仍落周边，记录地址栏完整最终URL（不要发送当前位置等私人信息），再定位服务端重定向。无需反复把已失败的网页二次跳转当主路径。

第二轮已发布：Sites v3，状态 succeeded，部署 `appgdep_6aa518c7e8a88191aa2f495ea45a25c3`，提交 `172ac81792bf909a427ef5b4bbd5860803526fce`。本地协议测试与完整页面模拟DOM切换测试通过；未把模拟DOM当真机复测。

[第二轮高德测试入口](https://routepilot-navigation-lab.season1016.chatgpt.site/spike04.html?trip_id=rp-spike04-demo-v1&segment=2&provider=amap)


## 14. 最终确认与结项归档

2026-09-12，用户明确确认：高德完整路线严格保持 **杭州→乌镇→南浔→西塘→上海** 的顺序，并能够进入导航。证据为用户真机反馈，不是代理亲自操作。当前样本是5个总点、3个途经点；已验证该样本完整交付、有序接收和导航启动，不能写成途经点最大值3，不能外推8点或全平台通过。

**本次Spike按用户要求结项，不再等待补测。** 未完成的跨平台/版本、最大容量、Universal Link专项验证及百度网页故障作为后续产品限制保留，不阻塞本次归档。微信内直接唤起与跳出微信后浏览器唤起仍要区分；系统、浏览器和App具体版本没有提供，不补造。

最终兼容策略：高德完整路线为优先交付路径；腾讯和百度单段直达App为备用；腾讯网页仅用于查看，网页二次跳App/小程序丢参数；百度网页落“周边”页，保留故障记录，不作为可靠回落。RoutePilot保留完整行程，失败时可按段导航/复制目的地。此次确认未证明原道路折线、ETA或实际驾驶完成。

原型保持当前公开部署，不再改动或重新发布；归档不代表关闭网站。用户要求结束的是本聊天任务。

- [最终用户确认](spike-04-navigation-evidence/final-confirmation.json)
- [RoutePilot归档索引](routepilot/technical-spike-04-archive.md)
- [百度网页失败截图](spike-04-navigation-evidence/baidu-web-failure-user-screenshot.jpg)（仅本地档案，不发布到网站）
