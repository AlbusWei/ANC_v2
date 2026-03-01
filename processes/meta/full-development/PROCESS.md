# full-development - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.3.0`
- Objective 引用：`obj-m3-full-development-loop`

## 流程目标（自然语言）

该流程是 ANC 内部产品孵化主线在运行时的落地骨架，负责把 Objective/Spec/Test/Implement/Verify/Lifecycle/Release/Evolution 串成可执行闭环。它的目标不是“完成一次开发”，而是沉淀一条可复用、可回放、可持续演进的端到端交付链。

## 协作编排原则

1. 主线必须保持 `Objective -> Spec -> Test -> Implement -> Verify -> Lifecycle -> Release -> Evolution` 连续闭合，禁止跳段直达实现或发布。
2. 每个阶段交付物必须具备下一阶段可直接消费的语义，不允许仅交“占位引用”。
3. `p5` 是主门禁分叉点：未通过时仅允许回退 `p4` 修订，不允许绕过门禁推进。
4. `p6/p7` 属于治理与运营收口，只有在门禁结论为 pass 时才可继续执行。
5. `p8` 必须把运行反馈回灌为下一轮输入，确保流程不是一次性交付而是持续演化。

## 阶段语义定义

### p1 objective-intake-and-scope

- 执行角色：`architect`
- 阶段目的：澄清目标并形成范围基线，为后续规格编写提供稳定输入。
- 输入语义：objective_context_ref,input_payload。
- 完成标准：必须产出 objective_ref 与 scope_baseline_ref。
- 交接说明：将 objective_ref 与 scope_baseline_ref 交接给 p2。
- 执行单元：`subprocess:objective-scope-baseline`。

### p2 spec-authoring

- 执行角色：`architect`
- 阶段目的：将目标与范围基线收敛为可执行规格。
- 输入语义：objective_ref,scope_baseline_ref。
- 完成标准：必须产出 spec_ref，并可追溯到 p1 输入。
- 交接说明：将 spec_ref 交接给 p3。
- 执行单元：`subprocess:spec-authoring-contract`。

### p3 quality-gate-preparation

- 执行角色：`qa`
- 阶段目的：围绕规格构建测试准备包，明确后续验证基线。
- 输入语义：spec_ref。
- 完成标准：必须产出 test_plan_ref 与 preparation_bundle_ref。
- 交接说明：将 test_plan_ref 与 preparation_bundle_ref 交接给 p4。
- 执行单元：`subprocess:quality-gate-preparation`。

### p4 implementation-execution

- 执行角色：`kernel-dev`
- 阶段目的：在规格与测试基线约束下完成实现与候选产物。
- 输入语义：spec_ref,test_plan_ref。
- 完成标准：必须产出 implementation_ref 与 candidate_artifacts_ref。
- 交接说明：将 candidate_artifacts_ref 交接给 p5。
- 执行单元：`subprocess:implementation-execution-core`。

### p5 quality-gate-evaluation

- 执行角色：`qa`
- 阶段目的：执行质量门禁评测并形成统一门禁结论。
- 输入语义：candidate_artifacts_ref,preparation_bundle_ref。
- 完成标准：必须产出 final_gate_verdict_ref，且门禁结论可解释。
- 交接说明：若门禁通过，则将 final_gate_verdict_ref 交接给 p6。
- 执行单元：`subprocess:quality-gate-evaluation`。

### p6 lifecycle-gate-sync

- 执行角色：`admin`
- 阶段目的：完成生命周期治理与 registry 同步前置校验。
- 输入语义：final_gate_verdict_ref,lifecycle_target。
- 完成标准：必须产出 lifecycle_transition_ref 与 registry_sync_ref。
- 交接说明：将 lifecycle_transition_ref 与 registry_sync_ref 交接给 p7。
- 执行单元：`subprocess:lifecycle-review`。

### p7 release-packaging

- 执行角色：`admin`
- 阶段目的：完成发布打包与回滚包准备。
- 输入语义：candidate_artifacts_ref,final_gate_verdict_ref,lifecycle_transition_ref,registry_sync_ref。
- 完成标准：必须产出 release_package_ref 与 rollback_bundle_ref。
- 交接说明：将发布产物与反馈证据交接给 p8。
- 执行单元：`subprocess:release-packaging-governed`。

### p8 evolution-feedback-planning

- 执行角色：`architect`
- 阶段目的：基于发布与运行反馈形成下一轮演化计划。
- 输入语义：release_package_ref,final_gate_verdict_ref,lifecycle_transition_ref,runtime_feedback_ref。
- 完成标准：必须产出 improvement_plan_ref 与 retro_report_ref。
- 交接说明：将演化计划回填给发起方作为下一轮输入。
- 执行单元：`subprocess:evolution-feedback-planning`。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `p5`。
- `p5` 在 `failure` 条件下流转到 `p4`（条件：iterations < 2）。
- `p5` 在 `success` 条件下流转到 `p6`（条件：gate_decision == pass）。
- `p6` 在 `success` 条件下流转到 `p7`。
- `p7` 在 `success` 条件下流转到 `p8`。
- `p8` 在 `success` 条件下流转到 `end`。

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
