# RoutePilot｜Technical Spike 03：路线优化算法验证

日期：2026-09-14（Asia/Shanghai）  
**状态：PASS；算法验证完成，等待归档。**

本轮复用工作区已有的可复用优化器，用 Spike 02 的 2026-09-14 鉴权补测真实矩阵重新执行；新增补测回归测试、来源核验和独立复现入口。没有开发产品或进入 Spike 04。旧报告保存在 [previous-report.md](spike-03-evidence/rerun-2026-09-14/previous-report.md)，其中 9 月 12 日的路线和性能数字不代表本轮结果。

## 1. 验收范围与点数定义

- fixed start；end=None 为开放终点，指定 end 为固定终点，end=start 支持回起点。
- 可排列 waypoint 为 3–8 个，不含固定起终点；fastest 最小化秒，shortest 最小化米。
- 5 地旅行 = 起点杭州 + 3 waypoint（乌镇、西塘、南浔）+ 终点上海，枚举 3!=6 条路线。
- 3/5/8 waypoint 性能分别使用 5/7/10 个总地点；不会把 8 个总地点误报成 8 waypoint。
- 另列 3 个总地点的两条顺序作为小规模算术验证。它只有 2 waypoint，低于 V1 接口的 3 waypoint 下限，因此使用独立枚举检查，不冒充 V1 接口用例。3 waypoint 下限另用真实开放路线验证。

## 2. 真实矩阵来源与转换

来源：[assembled-matrix.json](spike-02-evidence/supplement-2026-09-14/assembled-matrix.json)；原始响应：[recovery-probe.json](spike-02-evidence/supplement-2026-09-14/recovery-probe.json)。

核对了 matrix-row-0 至 matrix-row-4 五份原始 MCP 成功响应（status=0、is_error=false），逐项确认全部 25 单元、每行起点与共同目的地顺序一致。五行采样约为北京时间 16:52:55 至 16:53:16，属于分批非原子快照；地点坐标沿用历史 POI。完整 request_id、采样时间及源文件 SHA-256 写入本轮 results.json。

地点索引：0 杭州（杭州东站）、1 南浔古镇、2 乌镇、3 西塘古镇、4 上海（虹桥站）；具体停车场和坐标沿用 Spike 02。时间单位秒、距离单位米。

原始对角线含非零值；只在内存输入副本中把对角线归零，原始证据不修改。合法路线不走 i→i，因此不影响任何路线成本。20 条非对角有向边全部保留，没有对称化、缺失补零或虚构真实路段。

真实非对称例：杭州→南浔 84,284 米 / 4,694 秒；南浔→杭州 82,537 米 / 5,215 秒。

源矩阵 SHA-256：`5e77bf15ee45139c77ee3b26a6fc6c397c43af393729e2481588edd712e2bf52`。

## 3. 接口与算法

```python
from routepilot import optimize_route
result = optimize_route(
    start=0, waypoints=[2, 3, 1], end=4,
    time_matrix=duration_s, distance_matrix=distance_m,
    objective="fastest",
)
```

实现：[routepilot/optimizer.py](../routepilot/optimizer.py)。只依赖 Python 标准库，Python 3.10+。两份同序 N×N 矩阵分别传入，语义等价于一个含 time/distance 的 matrix 参数。

使用 Exhaustive Search / Brute Force：逐一枚举 k! 个 waypoint 排列，前置固定起点、按需追加终点，逐段按 i→j 累加时间和距离。fastest 比较（时间、距离、索引序列），shortest 比较（距离、时间、索引序列），保证并列时结果确定。不把秒与米混成加权分数。

原因：8!=40,320，当前规模可以完整枚举；实现简单、结果可审计，也可作为未来近似算法的小规模精确基准。每个合法访问顺序对应一个排列，枚举覆盖所有合法路线，因此返回当前静态矩阵与约束下的全局最优。该证明不需要矩阵对称。

输出 original / optimized 各含 order、total_duration、total_distance；savings 同时包含双指标绝对值与百分比，另含 candidates_evaluated。节省=(原值−优化值)/原值×100；原值为0时百分比为null；副目标变差保留负数。

拒绝重复 waypoint、越界或布尔索引、非法目标、非完整方阵、负值、NaN、Infinity、缺失边、非零对角线等输入；不修改输入。缺失/不可达成本需要上游明确处理。

## 4. 5 地真实旅行结果

原始顺序：**杭州→乌镇→西塘→南浔→上海**。固定杭州出发、上海结束。

| 目标 | 优化顺序 | total_duration 秒（原→优） | total_distance 米（原→优） | 时间节省 | 距离节省 |
| --- | --- | ---: | ---: | ---: | ---: |
| fastest | 杭州→南浔古镇→乌镇→西塘古镇→上海 | 15912→12954 | 293861→229985 | 2958 秒 / 18.59% | 63876 米 / 21.74% |
| shortest | 杭州→乌镇→南浔古镇→西塘古镇→上海 | 15912→13233 | 293861→219289 | 2679 秒 / 16.84% | 74572 米 / 25.38% |

fastest 预计节省49分18秒；shortest 预计节省74.572公里。两目标结果不同，说明 V1 必须保留目标选择。最快路线比最短距离路线快279秒，但长10.696公里。

## 5. 小规模、开放终点与非对称验证

3 个总地点的真实子矩阵：杭州→南浔→乌镇为6,547秒 / 102,509米；杭州→乌镇→南浔为6,050秒 / 88,603米。完整枚举两条顺序后，两目标均选择后者；节省497秒（7.59%）和13,906米（13.57%）。此项为参考枚举算术校验，V1接口用例见下表。

所有真实接口用例都同时保存原顺序、最佳顺序与全部候选，详见 results.json。

| Case | 目标 | 原顺序→最佳顺序 | 时间 秒（原→优） | 距离 米（原→优） | 时间 / 距离节省% |
| --- | --- | --- | ---: | ---: | ---: |
| real_three_waypoints_open | fastest | [0, 3, 2, 1]→[0, 1, 2, 3] | 9688→9460 | 190795→157019 | 2.35 / 17.70 |
| real_three_waypoints_open | shortest | [0, 3, 2, 1]→[0, 2, 1, 3] | 9688→9739 | 190795→146323 | -0.53 / 23.31 |
| real_five_open | fastest | [0, 2, 3, 1, 4]→[0, 1, 2, 3, 4] | 15912→12954 | 293861→229985 | 18.59 / 21.74 |
| real_five_open | shortest | [0, 2, 3, 1, 4]→[0, 2, 1, 3, 4] | 15912→13233 | 293861→219289 | 16.84 / 25.38 |
| real_reverse_fixed_end | fastest | [4, 1, 3, 2, 0]→[4, 3, 2, 1, 0] | 16147→13024 | 292747→228263 | 19.34 / 22.03 |
| real_reverse_fixed_end | shortest | [4, 1, 3, 2, 0]→[4, 3, 1, 2, 0] | 16147→13283 | 292747→215940 | 17.74 / 26.24 |
| real_return_to_start | fastest | [0, 3, 2, 1, 0]→[0, 1, 2, 3, 0] | 14903→14860 | 273332→272195 | 0.29 / 0.42 |
| real_return_to_start | shortest | [0, 3, 2, 1, 0]→[0, 3, 1, 2, 0] | 14903→15162 | 273332→261009 | -1.74 / 4.51 |

## 6. 测试与交叉核验

本轮 **11 个测试方法全部通过**。原有8项覆盖旧真实快照、闭环、开放非对称目标冲突、对称矩阵、并列、零成本、输入不变性和非法输入。新增3项覆盖9月14日原始来源、有向边、真实双目标精确数值、节省比例、开放终点与反向旅行。

独立子集动态规划 oracle 与生产穷举实现交叉核验：随机种子303，k=3…8 × 开放/固定/闭环 × 两目标，共36组随机有向子案例；新增真实快照也与该 oracle 比较。测试 oracle 不调用生产计分辅助函数。补测脚本另保存10个真实目标用例的全部候选并核对最小值和 k! 数量。

代码沿用已有实现，本轮没有声称重新经历历史 TDD 过程。证据：[unit-tests.txt](spike-03-evidence/rerun-2026-09-14/unit-tests.txt)。

## 7. 性能与复杂度

环境：Python 3.11.8，macOS-15.7.9-x86_64-i386-64bit。每组预热1次、顺序重复30次；perf_counter_ns 计时整个函数，包括校验、双指标求和、排序和结果构造，排除文件/网络/解释器启动。P95为排序第29个样本。

3 waypoint 用真实5×5矩阵；5和8 waypoint 使用固定 seed=303 的合成有向矩阵，只验证计算规模，不宣称已获得7/10地点真实地图矩阵。全部输入和原始30次样本已保存。

| waypoint | 总地点 | 候选数 | 目标 | min ms | median ms | P95 ms | max ms |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 3 | 5 | 6 | fastest | 0.019 | 0.019 | 0.046 | 0.091 |
| 3 | 5 | 6 | shortest | 0.019 | 0.020 | 0.035 | 0.054 |
| 5 | 7 | 120 | fastest | 0.185 | 0.190 | 0.314 | 0.375 |
| 5 | 7 | 120 | shortest | 0.184 | 0.185 | 0.212 | 0.494 |
| 8 | 10 | 40320 | fastest | 67.803 | 71.236 | 80.324 | 86.665 |
| 8 | 10 | 40320 | shortest | 70.133 | 76.042 | 96.128 | 113.870 |

复杂度：时间 O(N²+k·k!)，含全矩阵校验；额外空间 O(k)，输入矩阵 O(N²)。生产函数流式保留当前/最佳路线；验证脚本为审计保存小规模全部候选，不属于生产函数空间开销。

8 waypoint 两目标分别调用，中位数约71–76ms；本机单进程计算可行。实际服务并发、设备差异、地图采集耗时不在此次验收内；不将该性能当作线上SLA。

## 8. OR-Tools / heuristic 迁移判断及 V1 影响

V1 保留3–8 waypoint穷举。9/10/11 waypoint候选为362,880 / 3,628,800 / 39,916,800，未实测这些规模。超过8 waypoint时先评估子集DP（O(k²2^k)时间、O(k2^k)空间）或近似方案，不直接放开阶乘搜索上限。

工程建议：当目标部署环境的P95持续超过预设算法预算（例如500ms，属于建议而非承诺），或增加时间窗、多车辆、容量等约束时，重新评估求解器。OR-Tools 提供路由求解及局部搜索/时间限制；不能默认其启发式结果是全局最优，应报告求解状态并以本次穷举作小规模质量基准。[官方TSP说明](https://developers.google.com/optimization/routing/tsp)、[搜索选项](https://developers.google.com/optimization/routing/routing_options)（本轮已查阅）。

本次证明：真实矩阵→确定性全局最优访问顺序→时间/距离与节省报告的算法链成立。仅对给定静态快照和已选路段成立，shortest不是重新搜索整个道路网络。分批采样、未来交通变化、停留/停车时间、营业时间均不在模型内。Spike 02矩阵数量边界仍待补，不影响本次5地静态算法通过。

## 9. 交付与复现

```bash
python3 -m unittest discover -s tests -v
python3 -m scripts.rerun_spike03
```

从项目根目录执行；无需第三方依赖。第二条会更新本轮 results.json 和测试日志，性能再次运行会变化，报告表格对应本次保存的样本。旧 scripts/run_spike03.py 仍复现9月12日历史数据，不是本轮入口。

- 正式报告：docs/technical-spike-03.md
- 优化器：routepilot/optimizer.py
- 原有测试：tests/test_optimizer.py；补测测试：tests/test_spike03_supplement.py
- 本轮入口：scripts/rerun_spike03.py
- 本轮证据：docs/spike-03-evidence/rerun-2026-09-14/results.json
- 原始输入：docs/spike-02-evidence/supplement-2026-09-14/assembled-matrix.json、recovery-probe.json
- Final Archive Summary：docs/spike-03-evidence/rerun-2026-09-14/final-archive-summary.md

**停止于 Spike 03，等待归档。**
