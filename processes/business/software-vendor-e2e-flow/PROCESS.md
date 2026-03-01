# software-vendor-e2e-flow - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.1.0`
- 生命周期目标：`draft`
- Objective 引用：`obj-business-software-vendor-e2e-flow`

## 流程目标（自然语言）

该流程位于“外部软件交付”主线，职责是把客户商机输入、需求澄清、合同基线、交付迭代、验收交接和后续支持串成一个可审计闭环。它解决的问题是外部交付常见的“前段文档化、后段直连发布”断裂，要求交付阶段必须复用内部 canonical（`full-development`）能力，确保质量门禁、生命周期治理和 registry 同步不被绕过。对上下游的价值是：上游可拿到明确合同边界和风险约束，下游可获得带门禁证据和回滚能力的交付产物。

## 协作编排原则

1. 外部主线不是内部主线的平行替代，`delivery-iterations` 必须显式复用 `full-development`，禁止脚本直连发布。
2. 合同基线与交付迭代必须连续衔接，任何跨段跳转视为旁路并触发 Fail-Closed。
3. 客户验收、部署交接、支持反馈必须保留可追溯输出引用，不能只输出口头结论。
4. 生命周期结论在本回合上限为 `review`，越级到 `active` 视为违规。

## 阶段语义定义

### p1 lead-intake

- 执行角色：`architect`
- 阶段目的：把商机输入收敛为可执行目标上下文。
- 输入语义：`lead_context_ref`、`customer_constraints_ref`。
- 完成标准：必须产出 objective/scope 基线引用并可追溯。
- 交接说明：交接给 `p2`。

### p2 discovery-analysis

- 执行角色：`architect`
- 阶段目的：澄清需求与约束边界。
- 输入语义：`objective_ref`、`scope_baseline_ref`。
- 完成标准：必须形成 `discovery_baseline_ref`。
- 交接说明：交接给 `p3`。

### p3 solutioning-and-estimation

- 执行角色：`architect`
- 阶段目的：输出方案与估算规格。
- 输入语义：`discovery_baseline_ref`。
- 完成标准：必须产出 `spec_ref`。
- 交接说明：交接给 `p4`。

### p4 contract-baseline

- 执行角色：`architect`
- 阶段目的：固化合同边界与风险约束。
- 输入语义：`spec_ref`。
- 完成标准：必须产出 `contract_baseline_ref`。
- 交接说明：交接给 `p5`。

### p5 delivery-iterations

- 执行角色：`bpm`
- 阶段目的：执行交付迭代并复用 canonical `full-development`。
- 输入语义：`contract_baseline_ref`、`objective_ref`、`lifecycle_target`。
- 完成标准：必须产出 `final_gate_verdict_ref`、`lifecycle_transition_ref`、`registry_sync_ref`、`release_package_ref`。
- 交接说明：交接给 `p6`。
- 复用硬约束：`delivery-iterations -> full-development`，若缺失则 Fail-Closed。

### p6 customer-acceptance

- 执行角色：`qa`
- 阶段目的：完成客户验收证据收敛。
- 输入语义：`release_package_ref`、`final_gate_verdict_ref`。
- 完成标准：必须产出 `customer_acceptance_ref`。
- 交接说明：交接给 `p7`。

### p7 deployment-and-handover

- 执行角色：`admin`
- 阶段目的：完成部署交接与回滚包绑定。
- 输入语义：`customer_acceptance_ref`。
- 完成标准：必须产出 `deployment_handover_ref`。
- 交接说明：交接给 `p8`。

### p8 support-and-feedback

- 执行角色：`architect`
- 阶段目的：沉淀交付后支持反馈并回灌下一轮。
- 输入语义：`deployment_handover_ref`、`runtime_feedback_ref`。
- 完成标准：必须产出 `support_feedback_ref`。
- 交接说明：回填给发起方。

## 控制流与回退

- 主链：`p1 -> p2 -> p3 -> p4 -> p5 -> p6 -> p7 -> p8 -> end`。
- 返工：`p5` 失败可回流 `p3`（最多 1 次）。

## Fail-Closed 触发条件

1. `delivery-iterations` 未复用 `full-development`。
2. 缺失 `final_gate_verdict_ref/lifecycle_transition_ref/registry_sync_ref` 任一关键证据。
3. 尝试绕过交付迭代直接执行发布。
4. 尝试越级生命周期到 `active`。
