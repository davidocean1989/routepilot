# 本地运行 MVP

Python 3.11+，在仓库根目录：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: -r requirements.lock
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --no-access-log
```

API 文档：`http://127.0.0.1:8765/docs`，健康检查：`/health`。

配置见 `.env.example`。变量通过启动环境注入，本程序不自动加载 `.env`。SQLite 默认在 `data/trips.sqlite3`。不要把数据库、环境文件或服务端 Key 提交到仓库。

测试：`.venv/bin/python -m pytest -q`。

## 完整离线演示

```sh
ROUTEPILOT_MAP_MODE=demo .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --no-access-log
.venv/bin/python scripts/smoke.py http://127.0.0.1:8765 --full
```

此模式只接受杭州/杭州东站、南浔/南浔古镇、乌镇、西塘/西塘古镇、上海/上海虹桥站或样本 POI 全名。数据是 2026-09-14 历史快照，不是实时路况；没有历史道路折线。

真实模式设置 `TENCENT_MAP_KEY` 后使用 `ROUTEPILOT_MAP_MODE=tencent`。每次解析/优化在同一任务内建立并关闭 SSE 会话，默认调用间隔 5 秒、整体查询预算 180 秒；单进程运行（不要加多个 workers）。10 地点规模的实时配额和性能尚未验收。
