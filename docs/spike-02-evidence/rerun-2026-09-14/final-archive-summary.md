Final Archive Summary — RoutePilot Technical Spike 02（重新执行版）
状态：PARTIAL。2026-09-14 已进行真实 MCP 调用；有效矩阵验收因缺少腾讯位置服务 Key 阻塞，尚未完成全部验收。
测试环境：macOS 15.7.9 x86_64，Python 3.12.14，MCP SDK 2.2.0；腾讯官方 SSE，TencentMapMCPWebService 1.2.0，协议 2025-11-25。无 Key。沙箱 DNS 失败后获联网权限，成功连接。
测试案例：initialize、tools/list、杭州→南浔 1×1、南浔→杭州 1×1、杭州/南浔/乌镇/西塘/上海 5×5。坐标沿用历史腾讯 POI，未刷新。
关键返回：发现 15 个工具，包括 matrix、directionDriving；matrix 必填 from/to/mode 字符串。三次矩阵均 is_error=true，content 文本 Invalid Key，无 distance/duration。失败调用耗时分别 98.37、24.07、96.13 ms，不代表成功 API 延迟。
关键发现：原生 matrix 存在；有效 origins/destinations 数量、当前矩阵完整性、双向差异、成功延迟、账号配额与频控未完成本轮验证。官方参考说明矩阵米/秒及多对多每侧≤50、乘积≤625，属于文档信息而非本轮边界实测。历史成功结果保留但不计作本轮通过。
对 V1 影响：原生矩阵接入方向可继续验证，当前不能批准数据能力 PASS。备用设计为缺工具时 20 条有向 directionDriving 调用；原生矩阵受限时五个 1×4 分批。鉴权错误不能用备用接口绕过。
正式文件：/Users/davidocean/.codex/.chatgpt-projects/g-p-6a7c3b914b308191af071c856c131f09/docs/technical-spike-02.md
本轮证据：/Users/davidocean/.codex/.chatgpt-projects/g-p-6a7c3b914b308191af071c856c131f09/docs/spike-02-evidence/rerun-2026-09-14/
待办：提供私人 Key 配置路径或可用腾讯 MCP，补齐有效鉴权矩阵及边界测试。此次仅保存本地文件，未推送 GitHub。未进入 Spike 03、未执行优化算法。请仅记录此阶段性结果，等待补测及归档决定，不启动后续 Spike。
