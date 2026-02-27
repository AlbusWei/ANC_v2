# quality-gate-evaluation - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.3.0`
- Objective 引用：`obj-m1-unified-quality-gate`

## 流程目标（自然语言）

该流程负责汇总 objective/subjective/regression 三类评测，形成统一门禁结论并分流 hold 治理。它在架构中的角色是质量决策中枢，决定变更是否可进入生命周期迁移。对外结论使用 `gate_decision`，运行时治理状态使用 `runtime_gate_state`。

## 协作编排原则

1. 该流程是统一质量决策中枢，负责将多维评测收敛为单一门禁结论。
2. 客观、主观、回归三类评测应保持可解释分工，避免结论来源不透明。
3. 统一结论必须可直接驱动后续 lifecycle 决策，不能停留在描述性报告。
4. hold 分流必须纳入治理子流程，确保异常路径与正常路径同等可控。

## 阶段语义定义

### p1 run-objective-evaluation

- 执行角色：`qa`
- 阶段目的：执行客观评测 profile。
- 输入语义：preparation_bundle_ref + actual_output_refs。
- 完成标准：必须产出 objective_eval_ref，并满足“目标评测结论可解析且可追溯”。
- 交接说明：将 objective_eval_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:quality-gate-evaluation:p1`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.evaluation-runner`，穿透执行策略：允许（同 Actor 场景）。

### p2 run-subjective-evaluation

- 执行角色：`qa`
- 阶段目的：默认执行盲评主观评测。
- 输入语义：preparation_bundle_ref + actual_output_refs + subjective_plan。
- 完成标准：必须产出 subjective_eval_ref，并满足“主观评测记录包含 seed 轮次与结论”。
- 交接说明：将 subjective_eval_ref 交接给 p3。
- 执行单元：`subprocess:inline-ap:quality-gate-evaluation:p2`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.evaluation-runner`，穿透执行策略：允许（同 Actor 场景）。

### p3 run-regression-evaluation

- 执行角色：`qa`
- 阶段目的：执行跨模块回归评测。
- 输入语义：preparation_bundle_ref + profile_set + actual_output_refs。
- 完成标准：必须产出 regression_eval_ref，并满足“回归报告包含模块级结论”。
- 交接说明：将 regression_eval_ref 交接给 p4。
- 执行单元：`subprocess:inline-ap:quality-gate-evaluation:p3`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.regression-runner`，穿透执行策略：允许（同 Actor 场景）。

### p4 aggregate-gate-decision

- 执行角色：`qa`
- 阶段目的：汇总形成统一门禁结论。
- 输入语义：objective_eval_ref + subjective_eval_ref + regression_eval_ref。
- 完成标准：必须产出 gate_decision + runtime_gate_state，并满足“门禁决策遵循统一 verdict 枚举与 P0 优先规则”。
- 交接说明：将 gate_decision + runtime_gate_state 交接给 initiator。
- 执行单元：`subprocess:inline-ap:quality-gate-evaluation:p4`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.verdict-normalizer`，穿透执行策略：允许（同 Actor 场景）。

### p5 govern-hold

- 执行角色：`bpm`
- 阶段目的：将 hold 案例路由至 hold 治理子流程并判定是否自动回测。
- 输入语义：hold_case_ref + final_gate_verdict_ref。
- 完成标准：必须产出 hold_resolution_ref + retest_recommendation，并满足“hold 案例在证据支撑下被解决或升级且自动回测路由可判定”。
- 交接说明：若 retest_recommendation=auto-retest 且预算未耗尽则回路到 p2，否则将 hold_resolution_ref 交接给 initiator。
- 执行单元：`subprocess:hold-governance`。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success && runtime_gate_state == hold` 条件下流转到 `p5`。
- `p4` 在 `success && runtime_gate_state != hold` 条件下流转到 `end`。
- `p5` 在 `success && retest_recommendation == auto-retest && auto_retest_cycles_remaining > 0` 条件下流转到 `p2`。
- `p5` 在 `success && (retest_recommendation == stop || auto_retest_cycles_remaining == 0)` 条件下流转到 `end`。

## 协作策略（运行态）

1. 协作模式：`phase-isolated-session`。
2. 分发运行时：`openclaw-required`。
3. 会话重置策略：`per-phase-reset`。
4. phase 交接以自然语言任务说明 + 引用交接为主，不依赖隐式会话记忆。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
