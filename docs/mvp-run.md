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
