# hotfix - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.2.0`
- Objective 引用：`obj-m3-hotfix-loop`

## 流程目标（自然语言）

该流程是线上高优问题的快速闭环，在压缩路径下仍强制保留测试门禁、生命周期校验与可回滚发布。其意义是实现“快修复”与“可治理”并存，避免应急改动破坏系统秩序。

## 协作编排原则

1. 该流程追求“快速修复且可治理”，速度不能以跳过门禁与回滚能力为代价。
2. hotfix 路径允许压缩分析深度，但必须保留规格、测试、门禁与生命周期收口。
3. 发布前必须同时具备通过门禁结论与回滚方案，避免不可逆应急发布。
4. 失败回路应在实现与评测间快速闭环，避免扩散到无界人工协调。

## 阶段语义定义

### p1 hotfix-intake

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：归一化 hotfix 目标、影响范围与回滚方向。
- 输入语义：本阶段主要消费以下输入：incident_context_ref。
- 完成标准：完成判据：必须产出 hotfix_objective_ref, impact_scope_ref, rollback_direction_ref，并满足“hotfix 入口产出明确且可执行”。
- 交接说明：交接要求：将 hotfix_objective_ref, impact_scope_ref, rollback_direction_ref 交接给 p2。
- 执行单元：`subprocess:hotfix-intake-normalization`。

### p2 scope-and-spec-fast-baseline

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：为 hotfix 形成范围基线与规格基线。
- 输入语义：本阶段主要消费以下输入：hotfix_objective_ref + impact_scope_ref。
- 完成标准：完成判据：必须产出 hotfix_scope_baseline_ref + spec_ref，并满足“范围与规格基线包含回滚及爆炸半径约束”。
- 交接说明：交接要求：将 hotfix_scope_baseline_ref + spec_ref 交接给 p3。
- 执行单元：`subprocess:hotfix-scope-spec-baseline`。

### p3 fast-test-preparation

- 执行角色：`qa`
- 阶段目的：本阶段围绕以下业务动作推进：准备面向 P0 风险的 hotfix 测试。
- 输入语义：本阶段主要消费以下输入：spec_ref。
- 完成标准：完成判据：必须产出 test_plan_ref + preparation_bundle_ref，并满足“test_plan_ref 明确关联 spec_ref”。
- 交接说明：交接要求：将 test_plan_ref + preparation_bundle_ref 交接给 p4。
- 执行单元：`subprocess:quality-gate-preparation`。

### p4 hotfix-implementation

- 执行角色：`kernel-dev`
- 阶段目的：本阶段围绕以下业务动作推进：实施修复候选方案。
- 输入语义：本阶段主要消费以下输入：spec_ref + test_plan_ref。
- 完成标准：完成判据：必须产出 implementation_ref + candidate_artifacts_ref，并满足“候选产物可追溯到实现输出”。
- 交接说明：交接要求：将 implementation_ref + candidate_artifacts_ref 交接给 p5。
- 执行单元：`subprocess:implementation-execution-core`。

### p5 hotfix-gate-evaluation

- 执行角色：`qa`
- 阶段目的：本阶段围绕以下业务动作推进：评估目标门禁与回归门禁。
- 输入语义：本阶段主要消费以下输入：candidate_artifacts_ref。
- 完成标准：完成判据：必须产出 final_gate_verdict_ref，并满足“门禁结论为 pass/fail 且证据完整”。
- 交接说明：交接要求：将 final_gate_verdict_ref 交接给 p6。
- 执行单元：`subprocess:quality-gate-evaluation`。

### p6 lifecycle-gate-sync

- 执行角色：`admin`
- 阶段目的：本阶段围绕以下业务动作推进：校验生命周期与 registry 交接包。
- 输入语义：本阶段主要消费以下输入：final_gate_verdict_ref。
- 完成标准：完成判据：必须产出 lifecycle_transition_ref + registry_sync_ref，并满足“生命周期与 registry 交接包完整”。
- 交接说明：交接要求：将 lifecycle_transition_ref + registry_sync_ref 交接给 p7。
- 执行单元：`subprocess:lifecycle-review`。

### p7 release-packaging

- 执行角色：`admin`
- 阶段目的：本阶段围绕以下业务动作推进：打包并发布 hotfix 版本。
- 输入语义：本阶段主要消费以下输入：candidate_artifacts_ref, final_gate_verdict_ref, lifecycle_transition_ref, registry_sync_ref。
- 完成标准：完成判据：必须产出 release_package_ref + rollback_bundle_ref，并满足“发布包包含回滚材料与门禁证据”。
- 交接说明：交接要求：将 release_package_ref + rollback_bundle_ref 交接给 initiator。
- 执行单元：`subprocess:release-packaging-governed`。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `p5`。
- `p5` 在 `failure` 条件下流转到 `p4`（条件：iterations < 1）。
- `p5` 在 `success` 条件下流转到 `p6`（条件：gate_decision == pass）。
- `p6` 在 `success` 条件下流转到 `p7`。
- `p7` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_iterations=1, from_phase=p5, to_phase=p4。
