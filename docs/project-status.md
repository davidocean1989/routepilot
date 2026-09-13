# RoutePilot 项目状态

核对日期：2026-09-13（Asia/Shanghai）。本文件记录本次同步核验结果，不替代原项目已确认的产品文档。

## GitHub 同步

- 目标：https://github.com/davidocean1989/routepilot
- 可见性：public；默认分支：main；本次初始化前为空仓库。
- 历史阻碍：连接器创建 README.md 返回 HTTP 403：Resource not accessible by integration；未据此认定 GitHub App 完全未安装。
- 已安装并校验 GitHub CLI，用户通过浏览器授权 davidocean1989；凭证保存于本机钥匙串，Git 已配置使用该登录态。仓库权限核验为 ADMIN / push=true。
- 本次初始提交包含 README、项目状态、Spike 01 报告和六份证据，以及文件校验清单；四份基础文档仍缺正式原文。未使用聊天中暴露的 token。

## 正式文档清单

| 路径 | 状态 |
| --- | --- |
| README.md | 本次初始提交收录 |
| docs/00-project-charter.md | pending source：已确认正式原文待回传 |
| docs/01-user-journey.md | pending source：已确认正式原文待回传 |
| docs/02-prd.md | pending source：已确认正式原文待回传 |
| docs/03-technical-design.md | pending source：已确认正式原文待回传 |
| docs/technical-spike-01.md | 本次初始提交收录报告及六份证据 |
| docs/project-status.md | 本次初始提交收录 |

缺失的四份基础文档未以占位文件或推测稿冒充。当前环境没有读取原 ChatGPT 完整对话的 read_thread 工具，项目 sources 目录为空。

## Spike 归档

- Spike 01：本地报告记载最小链路通过，归档日期 2026-09-12；本次原样复制报告与六份证据，未重跑地图接口。
- Spike 02：本次重跑 rebuilding / pending archive。本地有历史报告，但未确认对应本次重跑的最终归档摘要。
- Spike 03：本次重跑 rebuilding / pending archive。本地存在 2026-09-12 归档摘要与 ZIP；是否对应本次重跑待核对。
- Spike 04：本次重跑 rebuilding / pending archive。本地存在 2026-09-12 导航归档摘要与 ZIP，并存在另一份预定时间实验；需核对重跑版本及实验范围。

以上 pending 状态针对本次重跑版本核对，不否定已有本地历史归档。原始归档及发布副本均保留，未删除、覆盖。

## 后续追加

1. 回传四份基础文档的已确认原文，按清单中的路径同步，并记录版本及来源。
2. 后续使用本机已授权 GitHub 登录态同步，并在每次提交后读回验证。
3. Spike 02–04 每项最终摘要回传后，核对日期、范围、结论、限制及证据对应关系；每项单独提交正式报告与必要的脱敏证据。
4. 更新本状态表和 README 索引。归档完成与技术验收通过分别记录，不将未通过项写成通过。
5. Spike 04 明确区分“导航”与“预定时间”实验，保留已有历史归档。
