# RoutePilot｜一趟跑完

## MVP Build · 本地可运行

一趟跑完的最小 FastAPI + SQLite + HTML/CSS/Vanilla JS 版本位于本分支。支持创建行程、地点解析/确认、最快/最短排序、持久结果、腾讯地图 SDK 与逐段导航接口。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: -r requirements.lock
ROUTEPILOT_MAP_MODE=demo .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --no-access-log
```

打开 `http://127.0.0.1:8765/`，从杭州→上海样例开始。演示使用明确标注的2026-09-14历史数据；真实腾讯模式需配置私有服务端Key，地图展示/腾讯App跳转分别需要独立浏览器可见凭证。在线联调及真机验收尚未完成。

- [运行与配置](docs/mvp-run.md)
- [实施计划](docs/04-mvp-implementation-plan.md)
- [验收与边界](docs/mvp-build-report.md)


一天跑 6 个地方，怎么走最顺？

RoutePilot 是 Davidocean · AI Career 项目中的多地点出行路线规划实验。

## 正式项目文档

| 文档 | 版本 / 范围 |
| --- | --- |
| [项目立项书](docs/00-project-charter.md) | v0.2：背景、定位、用户、范围与目标 |
| [用户旅程](docs/01-user-journey.md) | 用户需求、完整流程与 User Stories |
| [PRD](docs/02-prd.md) | v0.1：功能需求与验收标准 |
| [技术设计](docs/03-technical-design.md) | v0.1：架构、算法、数据模型与技术栈 |
| [Technical Spike 01](docs/technical-spike-01.md) | 腾讯位置服务 MCP 最小链路报告及六份证据 |
| [项目状态](docs/project-status.md) | 同步进度、实验归档及后续事项 |

四份基础文档由项目所有者于 2026-09-14 回传，本仓库原样收录。它们是正式需求与设计基线，不表示全部功能已经实现或验收；后续实验带来的设计修订应单独记录。

Spike 02–04：本次重跑版本为 rebuilding / pending archive。本地存在历史实验报告及部分归档摘要，尚待核对是否对应本次重跑，不据此宣称本次重跑完成。

原始本地归档与回传文件均保留。文件 SHA-256 校验值见 [sync-manifest.json](sync-manifest.json)。

## Spike 04 导航归档（2026-09-14）

[正式报告](docs/technical-spike-04.md) · [证据](docs/spike-04-evidence/navigation-rerun-2026-09-14/) · [Final Archive Summary](docs/spike-04-evidence/navigation-rerun-2026-09-14/final-archive-summary.md)

本项已归档，技术结论PARTIAL；取代上文Spike 04 pending状态。无新增真机测试，未启动Spike 06。
