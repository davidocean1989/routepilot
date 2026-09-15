# Spike 06 来源与本阶段使用方式

本次 GitHub 基线没有 technical-spike-06.md。核对了本地同项目以下两份只读来源：

- docs/technical-spike-06.md：2026-09-12 历史归档。用户反馈 iPhone Safari → 腾讯 App → 正确起终点 → 导航启动成功；微信直接唤起无反应。未覆盖四段、Android、未安装、明确系统/App 版本。
- docs/spike-06-evidence/run-2026-09-15/preflight.md：本轮新验收未完成，新增真机 0，四段均 NOT_TESTED。历史反馈不可自动升级为本轮 PASS。

MVP 使用逐段原生 qqmap 路线链接与外部浏览器帮助。此次开发不更改手机验收状态，不把单元测试计为微信、Safari 或 App 实测。此说明用于追踪设计依据，不是新的 Spike 06 结项报告。
