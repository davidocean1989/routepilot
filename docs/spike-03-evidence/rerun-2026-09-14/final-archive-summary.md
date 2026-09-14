# Final Archive Summary — RoutePilot Technical Spike 03

状态：**PASS**。2026-09-14 使用 Spike 02 鉴权补测真实5×5矩阵重新验证完成，等待归档。

测试：11个测试方法全部通过；涵盖固定起点、可选终点、3–8 waypoint、fastest/shortest、非对称、闭环、错误输入；36组随机有向矩阵与独立DP交叉核对。3总地点另作两条候选的算术验证，5地真实旅行通过生产接口，3/5/8 waypoint完成性能测量。

真实原顺序：杭州→乌镇→西塘→南浔→上海，15,912秒 / 293,861米。

| 目标 | 最优顺序 | total_duration | total_distance | 时间节省 | 距离节省 |
| --- | --- | ---: | ---: | ---: | ---: |
| fastest | 杭州→南浔→乌镇→西塘→上海 | 12,954秒 | 229,985米 | 18.59% | 21.74% |
| shortest | 杭州→乌镇→南浔→西塘→上海 | 13,233秒 | 219,289米 | 16.84% | 25.38% |

性能中位数（fastest / shortest）：3 waypoint 0.019 / 0.020ms；5 waypoint 0.190 / 0.185ms；8 waypoint 71.236 / 76.042ms。8 waypoint枚举40,320条路线。5/8 waypoint使用合成性能输入，不冒充真实地图数据。

V1影响：穷举可支持3–8 waypoint的静态有向矩阵精确排序；时间复杂度 O(N²+k·k!)。超过8 waypoint或新增复杂约束时评估DP、OR-Tools或heuristic。最优只针对当前矩阵；不保证实际未来交通收益。

文件：
- docs/technical-spike-03.md
- routepilot/optimizer.py
- tests/test_optimizer.py
- tests/test_spike03_supplement.py
- scripts/rerun_spike03.py
- docs/spike-03-evidence/rerun-2026-09-14/results.json
- docs/spike-03-evidence/rerun-2026-09-14/unit-tests.txt
- docs/spike-03-evidence/rerun-2026-09-14/manifest.json

本轮未进行产品开发或进入Spike 04，完成后等待归档。
