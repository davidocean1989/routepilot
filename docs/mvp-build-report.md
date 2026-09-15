# MVP Build 交付记录

分支：feat/mvp-build。基线：08afd47fd05019e43e0dd544e64150f33397ab4c。

## M0

计划先于产品代码单独提交并推送：fb6473ee21c288bcade03e0654155935eca9c01f。

## M1

FastAPI 应用工厂、Trip/Pydantic 校验、SQLite WAL、创建/读取、健康检查、统一错误与请求编号。编辑令牌只保存 SHA-256，读取接口不暴露令牌。SQLite 更新使用 revision 条件更新，后续流程复用。

测试：`python -m pytest tests/test_api.py -q`，13 passed；覆盖重建应用后持久化、非法输入、未知行程、密钥不外泄等。

依赖：使用隔离 Python 3.11 环境，安装版本锁定在 requirements.lock。cryptography 最新源码包在本机缺 OpenSSL 编译依赖，使用预编译兼容包 48.0.1；未要求全局编译工具。上游 Starlette 对 AnyIO 的弃用提示由精确测试 warning filter 过滤。

下一步：M2 迁入已验证优化器并实现腾讯 MCP 数据与行程工作流。
