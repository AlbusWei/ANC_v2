# refactor - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.2.0`
- Objective 引用：`obj-m3-refactor-loop`

## 流程目标（自然语言）

该流程面向结构重整与技术债治理，确保重构从目标界定到规格、测试、实现与门禁评测形成闭环。它的系统意义是用治理化路径提升可维护性，同时守住行为不回归。

## 协作编排原则

1. 该流程面向结构优化，核心约束是“提升可维护性且不引入行为回归”。
2. 重构目标与范围必须先收敛，防止技术债治理演变为无界改造。
3. 回归验证是重构放行前置条件，不能以代码整洁度替代质量结论。
4. 生命周期收口必须在门禁通过后执行，保证状态迁移有证据支撑。

## 阶段语义定义

### p1 refactor-objective-and-scope

- 执行角色：`architect`
- 阶段目的：明确重构目标与范围基线。
- 输入语义：objective_context_ref + tech_debt_ref。
- 完成标准：必须产出 objective_ref + scope_baseline_ref，并满足“目标与非目标明确”。
- 交接说明：将 objective_ref + scope_baseline_ref 交接给 p2。
- 执行单元：`subprocess:objective-scope-baseline`。

### p2 refactor-spec-authoring

- 执行角色：`architect`
- 阶段目的：编写受架构约束的重构规格。
- 输入语义：objective_ref + scope_baseline_ref。
- 完成标准：必须产出 spec_ref，并满足“规格文档明确不变量边界与回滚方案”。
- 交接说明：将 spec_ref 交接给 p3。
- 执行单元：`subprocess:spec-authoring-contract`。

### p3 refactor-test-preparation

- 执行角色：`qa`
- 阶段目的：准备以回归验证为核心的测试。
- 输入语义：spec_ref。
- 完成标准：必须产出 test_plan_ref + preparation_bundle_ref，并满足“test_plan_ref 明确关联 refactor spec”。
- 交接说明：将 test_plan_ref + preparation_bundle_ref 交接给 p4。
- 执行单元：`subprocess:quality-gate-preparation`。

### p4 refactor-implementation

- 执行角色：`kernel-dev`
- 阶段目的：执行结构性重构改动。
- 输入语义：spec_ref + test_plan_ref。
- 完成标准：必须产出 implementation_ref + candidate_artifacts_ref，并满足“实现与规格及约束保持关联”。
- 交接说明：将 implementation_ref + candidate_artifacts_ref 交接给 p5。
- 执行单元：`subprocess:implementation-execution-core`。

### p5 refactor-gate-evaluation

- 执行角色：`qa`
- 阶段目的：执行目标与回归门禁检查。
- 输入语义：candidate_artifacts_ref。
- 完成标准：必须产出 final_gate_verdict_ref，并满足“回归结果明确且证据完整”。
- 交接说明：将 final_gate_verdict_ref 交接给 p6。
- 执行单元：`subprocess:quality-gate-evaluation`。

### p6 lifecycle-gate-sync

- 执行角色：`admin`
- 阶段目的：校验生命周期与 registry 同步包。
- 输入语义：final_gate_verdict_ref。
- 完成标准：必须产出 lifecycle_transition_ref + registry_sync_ref，并满足“registry 同步载荷与生命周期证据完整”。
- 交接说明：将 lifecycle_transition_ref + registry_sync_ref 交接给 initiator。
- 执行单元：`subprocess:lifecycle-review`。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `p5`。
- `p5` 在 `failure` 条件下流转到 `p4`（条件：iterations < 2）。
- `p5` 在 `success` 条件下流转到 `p6`（条件：gate_decision == pass）。
- `p6` 在 `success` 条件下流转到 `end`。

## 协作策略（运行态）

1. 协作模式：`phase-isolated-session`。
2. 分发运行时：`openclaw-required`。
3. 会话重置策略：`per-phase-reset`。
4. phase 交接以自然语言任务说明 + 引用交接为主，不依赖隐式会话记忆。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_iterations=2, from_phase=p5, to_phase=p4。
