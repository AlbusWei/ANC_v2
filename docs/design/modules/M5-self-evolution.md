# M5 — 自演化模块详细设计

> 版本: v0.3.1 | 建设优先级: P2

## 模块定位

以指标驱动持续改进，形成监控->分析->规划->开发->验证闭环。

## 模块边界

1. `M5` 负责改进提案与优先级，不直接替代开发执行与生命周期审批。
2. `M5` 通过 `M3` 承接改进实施，通过 `M4` 完成治理放行。
3. `M5` 复用 `M1` 测试能力做改进有效性验证。

## 组件

1. monitor
2. analyst
3. planner
4. evolution-loop
5. improvement-review

## 依赖关系（类型化）

1. 依赖 `M1`（`T`）：改进前后测试基线和效果判定。
2. 依赖 `M2`（`R/E`）：改进任务调度、实例追踪与证据归档。
3. 依赖 `M3`（`R`）：将提案落地为可执行开发任务。
4. 依赖 `M4`（`G`）：高风险改进审批、状态推进与回滚治理。
5. 依赖 `M6`（`E`）：风险登记与阶段看板同步。

## 与双主线关系

1. 内部主线将运行反馈接入 M5。
2. 外部主线的 support-and-feedback 复用 M5 改进机制。

## M5 -> M1 最小接入说明（Thread-3）

1. 最小接入目标：验证 `M5` 可调用 `M1` 门禁入口（`quality-gate-preparation` + `quality-gate-evaluation`）。
2. 运行级用例：`TC-M1-CHAIN-004`。
3. 用例证据：
   - `runtime_data/execution/evidence/quality-gate/runtime-validation-round-6-m1-closure/TC-M1-CHAIN-004/evidence_index.json`
   - `runtime_data/execution/evidence/quality-gate/runtime-validation-round-6-m1-closure/TC-M1-CHAIN-004/eval_output.json`
4. 结论口径：`M5` 当前已具备接入统一门禁入口的最小执行能力；后续线程再扩展提案编排与状态联动。

## Fail-Closed 规则

1. 指标不可比或证据缺失时，提案不得进入执行阶段。
2. 高风险改进未完成审批时，禁止下发到开发执行。
3. 改进后回归失败时，触发回滚或降级方案并升级 `owner -> bpm -> admin`。

## 风险与缓解

1. 风险：改进收益不可量化，导致“主观优化”。
缓解：强制引入改进前后指标基线与测试判据。
2. 风险：反馈闭环长，问题修复滞后。
缓解：通过 `M2` 证据链跟踪提案生命周期并设升级门限。

## 验收

- [ ] 提案可量化
- [ ] 改进可回滚
- [ ] 指标提升可验证
- [ ] 改进提案执行前后均具备可追溯证据
