# lifecycle-review - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`hr`
- 版本：`0.1.0`
- Objective 引用：`obj-m4-lifecycle-review-runtime`

## 流程目标（自然语言）

该流程负责资产生命周期迁移前的最终治理校验，确保 quality gate、状态迁移规则与 registry 一致性同时成立。其目标是让状态变化成为“有证据的治理动作”，而非单点人工修改。

## 协作编排原则

1. 生命周期迁移是治理动作，不是状态字段修改；必须有门禁与证据支撑。
2. 迁移前需同时校验请求合法性、前置条件与质量门禁结论。
3. 迁移记录与 registry 同步必须成对落盘，避免状态与目录分叉。
4. 任何校验失败均应阻断迁移，防止不合格资产进入下一生命周期。

## 阶段语义定义

### p1 validate-request

- 执行角色：`hr`
- 阶段目的：本阶段围绕以下业务动作推进：校验生命周期评审请求结构与字段完整性。
- 输入语义：本阶段主要消费以下输入：final_gate_verdict_ref + target_asset_ref + requested_transition。
- 完成标准：完成判据：必须产出 validated_request_ref，并满足“必填字段完整且引用可达”。
- 交接说明：交接要求：将 validated_request_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:lifecycle-review:p1`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p2 check-prerequisites

- 执行角色：`hr`
- 阶段目的：本阶段围绕以下业务动作推进：核查当前生命周期状态与迁移前置条件。
- 输入语义：本阶段主要消费以下输入：validated_request_ref + target_asset_ref + requested_transition。
- 完成标准：完成判据：必须产出 prerequisites_check_ref，并满足“迁移路径符合五态生命周期规则”。
- 交接说明：交接要求：将 prerequisites_check_ref 交接给 p3。
- 执行单元：`subprocess:inline-ap:lifecycle-review:p2`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p3 quality-gate

- 执行角色：`hr`
- 阶段目的：本阶段围绕以下业务动作推进：在迁移前确认门禁结论为 pass。
- 输入语义：本阶段主要消费以下输入：final_gate_verdict_ref。
- 完成标准：完成判据：必须产出 quality_gate_check_ref，并满足“质量门禁结论为 pass 且证据可追溯”。
- 交接说明：交接要求：将 quality_gate_check_ref 交接给 p4。
- 执行单元：`subprocess:inline-ap:lifecycle-review:p3`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p4 execute-transition

- 执行角色：`hr`
- 阶段目的：本阶段围绕以下业务动作推进：在门禁通过后记录生命周期迁移。
- 输入语义：本阶段主要消费以下输入：target_asset_ref + from_status + requested_transition。
- 完成标准：完成判据：必须产出 lifecycle_transition_ref，并满足“迁移记录包含 from/to 状态、actor 与证据引用”。
- 交接说明：交接要求：将 lifecycle_transition_ref 交接给 p5。
- 执行单元：`subprocess:inline-ap:lifecycle-review:p4`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p5 sync-registry

- 执行角色：`hr`
- 阶段目的：本阶段围绕以下业务动作推进：校验 registry 一致性并落盘同步记录。
- 输入语义：本阶段主要消费以下输入：lifecycle_transition_ref。
- 完成标准：完成判据：必须产出 registry_sync_ref + lifecycle_review_report_ref，并满足“registry 校验通过且同步证据已落盘”。
- 交接说明：交接要求：将 registry_sync_ref + lifecycle_review_report_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:lifecycle-review:p5`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.registry-validator`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `p5`。
- `p5` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
