# MVP Build 交付记录

分支：feat/mvp-build。基线：08afd47fd05019e43e0dd544e64150f33397ab4c。

## M0

计划先于产品代码单独提交并推送：fb6473ee21c288bcade03e0654155935eca9c01f。

## M1

FastAPI 应用工厂、Trip/Pydantic 校验、SQLite WAL、创建/读取、健康检查、统一错误与请求编号。编辑令牌只保存 SHA-256，读取接口不暴露令牌。SQLite 更新使用 revision 条件更新，后续流程复用。

测试：`python -m pytest tests/test_api.py -q`，13 passed；覆盖重建应用后持久化、非法输入、未知行程、密钥不外泄等。

依赖：使用隔离 Python 3.11 环境，安装版本锁定在 requirements.lock。cryptography 最新源码包在本机缺 OpenSSL 编译依赖，使用预编译兼容包 48.0.1；未要求全局编译工具。上游 Starlette 对 AnyIO 的弃用提示由精确测试 warning filter 过滤。

下一步：M2 迁入已验证优化器并实现腾讯 MCP 数据与行程工作流。

## M2

腾讯 MCP SSE 客户端、工具响应业务状态校验、3 次以内尝试、串行间隔、分行有向矩阵、POI 城市筛选与确认、真实道路差分折线及分钟→秒转换。Trip resolve/confirm/optimize 已接入，结果只读，冲突返回 409；上游失败保留已确认状态，缺道路几何时保存排序及明确警告。

原优化器、11 项原测试与原复核脚本从同项目本地归档逐字节迁入，见 `mvp-evidence/optimizer-provenance.json`。没有改算法。历史演示使用仓库 2026-09-14 真实采样矩阵，标记 historical_demo，未知地点不替换，实时服务失败不会回落演示。

验证：55 Python tests、64 原算法 subtests 通过。包含限流恢复、鉴权不重试、超时、矩阵缺边、方向性、单位、polyline、城市筛选、权限、状态机、持久化、版本冲突和流程失败保留。M1 HTTP smoke 已通过。M2 HTTP smoke 命令：`python scripts/smoke.py http://127.0.0.1:8766 --full`。

当前进程 TENCENT_MAP_KEY 未配置；本轮未真实调用腾讯，不将契约测试当作在线联调。默认真实模式缺配置明确 503。浏览器凭证与服务端凭证要求不同值。

下一步：M3 三页面、腾讯 JS 地图、NavigationAdapter 与浏览器交互验收。
