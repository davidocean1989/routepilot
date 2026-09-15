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

## 打开页面

服务启动后打开 `http://127.0.0.1:8765/`。点击样例→下一步→逐点确认→结果。结果 URL `/t/{trip_id}?segment=0` 只包含行程与段号，不包含编辑令牌。关闭整个浏览器会话后编辑令牌可能丢失，但结果链接仍可读取；未完成的 Trip 可重新创建。

## 真实地图运行配置

| 环境变量 | 用途 |
|---|---|
| TENCENT_MAP_KEY | 后端 MCP 权限，永不返回前端 |
| TENCENT_JS_KEY | 腾讯 GL JS SDK，浏览器可见，需配置允许的域名 |
| TENCENT_NAV_KEY | 腾讯 App URI referer，浏览器可见 |

浏览器两项必须与服务端 Key 不同，否则启动拒绝。空值不会让浏览器尝试使用服务端 Key。凭证应从腾讯控制台和私有终端提供，不要粘贴进仓库或聊天记录。

腾讯 SDK 的地图瓦片与道路明细需网络及有效权限；历史演示没有道路折线。方向查询的时间从分钟转换为秒，与 Matrix 秒严格区分，结果统计始终使用优化成本矩阵。

## 开发验证

```sh
.venv/bin/python -m pytest -q
node --test tests/web.test.cjs
.venv/bin/python scripts/smoke.py http://127.0.0.1:8765 --full
```

`--full` 会对当前配置模式发起真实的创建/解析/确认/优化请求：演示模式离线，真实模式消耗腾讯调用额度。只用公开样例地点做 smoke。代码不自动部署网站；部署前需要补齐私有Key、域名白名单、HTTPS与公开服务滥用控制。SQLite 文件需要持久磁盘并妥善备份，服务只运行一个 worker。
