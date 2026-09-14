# RoutePilot｜Technical Spike 04：H5 / 微信 / 地图 App Deep Link

复核日期：2026-09-14（Asia/Shanghai）  
技术状态：**PARTIAL**；本次可执行验证与报告整理已完成，**等待归档**。仅 Spike 04，未启动 Spike 06。

## 1. 结论与证据边界

从有序行程到地图的交付方案可行，但完整的“结果页 → 分享 → 微信 → 地图导航”尚无覆盖充分的实测证据。三家 Adapter 和分享逻辑本地回归通过；历史本地档案记录高德接收固定5站、保持顺序并进入导航。该记录是2026-09-12用户反馈的转存，本次未重新查证原对话或操作手机，不能当作本次真机测试。

**本次重要修正：腾讯新版官方 App URI 明确支持 passes，最多15个途经点。** 旧报告的腾讯多点“未知”已不适用于官方协议能力；现有 TencentMapAdapter 仍仅实现单段，多点尚未实现或实机验收。[腾讯 App 官方文档](https://lbs.qq.com/webApi/uriV1/uriGuide/uriMobileRoute)

未完成项包括：新分享链接在微信中保留参数、明确版本的iOS/Android对比、未安装App的实际表现、腾讯完整路线接收、百度Android多点接收、App实测最大容量及Universal Link。故整体不能评为PASS；也不应因覆盖不足判整个方案FAIL。

## 2. 环境与执行范围

- 本次：macOS / Darwin x86_64，随附Node运行时，实际版本与时间见 [local-tests.json](spike-04-evidence/navigation-rerun-2026-09-14/local-tests.json)。测试为Node VM协议执行、模拟DOM页面逻辑，不是完整浏览器渲染或手机测试。
- 官方文档：通过网页工具读取高德、百度、腾讯官方站点。腾讯旧App链接读取失败，沿官方链接找到新版并成功核对。
- 当前没有可用的手机操作会话；本次新增真机测试数量为0。没有新增部署或声称现有公共站点当前可用。
- 历史手机记录：离开微信后打开的浏览器，名称、系统版本、地图版本未记录。不能将其归为微信WebView直接成功或明确的iOS/Android兼容组合。
- 复用既有原型，不改产品代码、线上站点或旧归档。sources/参考材料未修改。

## 3. 地图协议及多途经点能力

“官方支持”表示参数合约存在；“本地通过”仅表示生成和解析符合检查；“历史反馈”表示本地已有用户实测转存。三者不得混用。数量指途经点，不含起终点。

| 地图/入口 | 官方文档结论 | 现有实现与证据 | 容量结论 |
|---|---|---|---|
| 腾讯 App，iOS/Android | qqmap://map/routeplan；passes支持多点，坐标纬度在前，每点以竖线结束；referer需开发者凭证 | 单段构造通过；历史反馈起终点带入。旧Adapter未实现passes | **官方最多15；实测上限未知** |
| 腾讯 Web | HTTPS routeplan提供起终点、coord_type、来源字段；所查表未列多点 | 历史网页可看，但网页再跳App/小程序丢端点 | Web多点未确认 |
| 高德 App，Android | amapuri://route/plan/；vian、vialons、vialats、vianames有多点合约 | 双平台协议构造通过；历史高德5站成功未绑定明确平台版本 | 未列数值上限 |
| 高德 App，iOS | iosamap://path；同类多点字段 | 固定样本：历史记录3个途经点顺序保持并能进入导航 | 历史样本为3，不是最大值3 |
| 高德 Web | navigation的via仅驾车可用，**最多1个** | 本例3个途经点不应使用Web完整交付 | 官方最多1 |
| 百度 Android H5 | bdapp://map/direction；表中列viaPoints JSON，navi节有嵌套数组示例 | 候选完整payload本地通过；direction是否接收该结构未真机证实 | 未确认数值上限 |
| 百度 iOS | baidumap://map/direction可做单段；所查页面未确认多点合约 | 历史单段App端点接收；原型不生成完整路线 | 未知 |
| 百度 Web | 本次沿用历史接口分析，无新增官方Web复核 | 历史落入“周边/生活服务”页，不能作为可靠导航回落 | 不用于完整交付 |

来源：[腾讯App](https://lbs.qq.com/webApi/uriV1/uriGuide/uriMobileRoute)、[腾讯Web](https://lbs.qq.com/uri_v1/guide-route.html)、[高德Android](https://lbs.amap.com/api/amap-mobile/guide/android/route)、[高德iOS](https://lbs.amap.com/api/amap-mobile/guide/ios/route)、[高德Web](https://lbs.amap.com/api/uri-api/guide/travel/route)、[百度Android](https://lbsyun.baidu.com/docs/webapi?title=mapadjustment/uri/andriod)、[百度iOS](https://lbsyun.baidu.com/docs/webapi?title=mapadjustment/uri/ios)。检索记录见 [official-sources.json](spike-04-evidence/navigation-rerun-2026-09-14/official-sources.json)。不保存含凭证的官方示例URL。

## 4. Navigation Adapter设计核验

代码：[navigation04.js](../routepilot-nav-test/dist/navigation04.js)。三个具名类均存在，统一接口为capabilities()、buildSegment(trip,index)、buildFullRoute(trip)，通过adapter(provider,os,credential)选择。输入含trip_id、revision、coordinateSystem、有序points；输出包含appUrl、webUrl、pointCount、reason、productionEnabled及navigationConfirmed。

职责划分合理：Adapter负责协议、坐标和容量能力；页面负责分享恢复、用户点击、失败帮助与记录。返回链接不等于导航已启动，原型所有交付均保持productionEnabled=false，navigationConfirmed=false。

当前限制与V1接入条件：

1. TencentMapAdapter需补充passes构造及15点上限校验，完成后才可标记为“已实现”。本次不以新文档发现冒充代码已支持。
2. capability应按地图、OS、浏览器、版本、证据记录，而不是全局品牌布尔值；maxWaypoints=null表示未知，不等于无限。
3. 高德有序数组数量必须一致；未知容量不得静默截断。百度Android实验结构保持待验，不外推iOS。
4. 现有代码仅固定演示行程，不是任意输入的生产Adapter。生产需补坐标范围、合法名称/分隔符、数量、空点集和行程版本校验。
5. 保持GCJ-02；腾讯组合坐标lat,lng，高德Web为lng,lat；百度显式gcj02。名称和JSON只编码一次，不跨地图使用POI ID。
6. 腾讯凭证由运行配置注入，不进入报告、分享链接或证据日志；本地测试使用占位输入。报告不复制原型内的凭证值。

## 5. H5交付流程核验

固定fixture：杭州东站 → 乌镇西栅景区1号停车场入口 → 南浔古镇1号停车场入口 → 西塘古镇景区第一地上停车场 → 上海虹桥站。5站、3途经点、4段，GCJ-02。该顺序用于交付对照，不代表本次重新运行了优化算法。

原型：[spike04.html](../routepilot-nav-test/dist/spike04.html)。分享路径示例：`/spike04.html?trip_id=rp-spike04-demo-v1&segment=2&provider=amap`。segment从0开始，此处为第3段。

| 流程节点 | 本次/历史证据 | 判断 |
|---|---|---|
| 优化结果 → Result Page | 原型使用固定fixture，没有接入实时优化输出 | 接口设计已分析，集成未验证 |
| Result Page → Share URL | 本地测试检查行程编号、段号、地图选择；未知/重复行程ID及非法段拒绝 | 本地通过 |
| Share URL → 微信打开 | 无本次手机；历史反馈未明确核对trip_id/segment | 未验证 |
| 微信 → 外部浏览器 → App | 历史记录三家单段端点接收，高德完整样本启动导航 | 有限历史证据 |
| 微信WebView → App | 无本次成功证据 | 未验证，不能与跳出微信混算 |
| App返回H5 | 页面代码保留行程、不自动切段；本次未实机验证返回 | 设计已检查，真机未验证 |

跨浏览器依靠URL恢复固定行程，localStorage记录不会跨浏览器同步。生产应以trip_id+revision读取稳定的只读行程快照，而非要求用户重新输入地点；未知/过期行程应明确报错。原型尚不能证明生产快照、权限或任意行程分享已完成。

## 6. 平台差异、未安装与微信限制

高德官方Web文档明确callnative可能无法在微信/QQ内置浏览器唤起。这个限制不能推广为所有地图或微信版本均不支持。[官方说明](https://lbs.amap.com/api/uri-api/guide/travel/route)

iOS/Android协议差异如上表，本次只验证链接构造。系统提示、用户取消、微信拦截及App未安装的真实表现均未新测。原型提供用户主动点击的链接；2200ms计时只显示帮助，visibilitychange只表示离开/回到页面，不能证明App已安装、路线正确或导航成功。

未安装或无响应时，应保留完整行程与当前段，提供外部浏览器打开说明、复制目的地、可用网页路线和其他地图选择。网页路线也可能重新诱导调App；腾讯网页历史只能可靠记为“可查看”，百度网页已有失败记录，不能将二者写成已通过的自动fallback。不得失败后直接跳最终终点遗漏途经点。

三家Universal Link / Android App Links的完整路线交付及安装/未安装回落本次均未验证。HTTPS网页、Scheme和Universal Link不是同一种机制。

## 7. 测试执行和历史结果

本次复跑两份既有测试，退出码均为0，完整输出、执行环境见 [local-tests.json](spike-04-evidence/navigation-rerun-2026-09-14/local-tests.json)。

- navigation04.cjs：24组单段构造（3地图×2系统×4段，每组有App/Web链接），高德/百度候选多点payload、协议、坐标、降级、分享解析。
- page04-feedback.cjs：模拟DOM执行地图切换、协议与标签、完整路线入口、失败网页降级展示及分享地图保留。

这两份测试不覆盖实际地图服务、系统唤起、微信访问或安装状态，也不覆盖新发现的腾讯passes。

历史证据转存：[高德最终确认](spike-04-evidence/navigation-rerun-2026-09-14/historical-final-confirmation.json)、[首轮反馈](spike-04-evidence/navigation-rerun-2026-09-14/historical-phone-feedback-round1.json)。腾讯网页二次跳转丢参数、百度网页落周边页均作为历史失败保留，不声称已修复。

容量后续验证方法（本次未执行）：按不同真实途经点数量核对输入和App接收数量、顺序、坐标及导航启动；腾讯应包含15和16点的边界，其他地图先测3、8等样本。通过N只能说明该版本至少接收N；不得从单个成功样本推断最大值。全平台矩阵至少覆盖3地图×2系统×2浏览器×2安装状态，共24组合；当前不能补造通过格。

## 8. Preferred Path / Fallback Path及V1影响

**Preferred Path：** H5保留完整行程 → 离开受限浏览器 → 用户点击高德完整路线 → 在App核对全部站点顺序并确认导航。优先建议基于本地历史5站反馈；具体版本组合仍需登记后才能对外承诺兼容。腾讯完整多点可作为下一候选，其官方15点容量不能代替实现或实测。

**Fallback Path：** H5保留有序行程 → 按当前段直达所选地图App → 用户返回后手动选下一段。无法唤起时用外部浏览器、其他已安装地图、复制目的地；网页只作为经验证可用的查看入口。百度网页不作为可靠回落。

对V1：保留地图可替换接口；不承诺微信内一键唤起三家，不承诺任意数量一次交付。将“打开App”“端点/途经点正确”“导航开始”分别验收。RoutePilot负责访问顺序，地图会重算道路、ETA并可能采用当前位置或本地偏好；不能承诺保持优化器道路折线或ETA。完整路线失败不能丢站；逐段进度不得由页面退到后台自动推进。

## 9. 文件与归档状态

本轮正式报告为本文件。证据目录：[docs/spike-04-evidence/](spike-04-evidence/)，本次新增集中在navigation-rerun-2026-09-14/；原目录中的experiment.json和verification-summary.json属于旧“预定时间”实验，未修改且不用于导航结论。历史导航证据仍在spike-04-navigation-evidence/。

旧报告备份为 [previous-report.md](spike-04-evidence/navigation-rerun-2026-09-14/previous-report.md)，仅保留历史文字，其原相对链接需以原docs目录解释。本报告取代旧报告当前状态和腾讯多点结论，不更改历史归档包。本次测试文件哈希见 [tested-files.json](spike-04-evidence/navigation-rerun-2026-09-14/tested-files.json)。

**Final Archive Summary：PARTIAL；macOS本地测试通过，无新增真机；高德有历史5站有序导航反馈，腾讯官方支持15途经点但原型未实现，百度Android多点待测；高德完整路线优先，逐段交付/复制目的地回落。报告完成，等待归档，不启动Spike 06。**
