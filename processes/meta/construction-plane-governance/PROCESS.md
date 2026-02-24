# construction-plane-governance - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`architect`
- 版本：`0.3.0`
- Objective 引用：`obj-m6-construction-plane-governance`

## 流程目标（自然语言）

该流程用于层/模块变更后的联动治理，确保设计文档、inventory、registry 与 OpenSpec 状态在同一轮次一致收敛。它在全局中的作用是维护“架构真相与运行资产同步”，避免出现设计与实现倒挂。

## 协作编排原则

1. 联动治理必须“同轮次收敛”：设计文档、inventory、registry、OpenSpec 不允许跨轮断裂更新。
2. 范围基线先行，先定义本轮边界与联动目标，再进入审计与改写。
3. 审计阶段需显式识别阻塞缺口，并把未解决问题落为可追踪项。
4. 收口阶段必须同时包含校验结果与责任归属，避免“有问题但无人负责”。
5. 该流程目标是维护架构真相一致性，而非追求文档数量或格式完整度。

## 阶段语义定义

### p1 scope-intake-and-baseline

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：设定本轮治理的范围与边界基线。
- 输入语义：本阶段主要消费以下输入：round_id + round_goal + change_scope_ref + changed_assets + linkage_targets + openspec_ref。
- 完成标准：完成判据：必须产出 scope_baseline_ref，并满足“范围基线包含模块边界与联动目标”。
- 交接说明：交接要求：将 scope_baseline_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:construction-plane-governance:p1`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p2 run-construction-audit

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：审计联动项完整性并识别阻塞缺口。
- 输入语义：本阶段主要消费以下输入：round_id + scope_baseline_ref + linkage_targets + changed_assets + openspec_ref。
- 完成标准：完成判据：必须产出 linkage_report_ref，并满足“联动报告包含缺项与阻塞风险”。
- 交接说明：交接要求：将 linkage_report_ref 交接给 p3。
- 执行单元：`subprocess:inline-ap:construction-plane-governance:p2`。该阶段采用临时 AP 语法，映射 skill 为 `sys.arch.construction-audit`，穿透执行策略：允许（同 Actor 场景）。

### p3 execute-linked-updates

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：在设计文档、清单与注册表中同步落盘联动更新。
- 输入语义：本阶段主要消费以下输入：round_id + linkage_report_ref + changed_assets。
- 完成标准：完成判据：必须产出 m6_update_bundle_ref + construction_plane_delta_ref + open_questions_ref，并满足“所有必需联动资产在同一轮次完成更新”。
- 交接说明：交接要求：将 m6_update_bundle_ref + construction_plane_delta_ref + open_questions_ref 交接给 p4。
- 执行单元：`subprocess:inline-ap:construction-plane-governance:p3`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p4 sync-openspec-state

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：执行 OpenSpec 同步并生成机器可读记录。
- 输入语义：本阶段主要消费以下输入：round_id + round_goal + openspec_ref + anc_design_refs + decision_snapshot_ref + sync_actor + trigger_mode + risk_level + checkpoint_count + commit_count + round_evidence_log_ref + output_ref。
- 完成标准：完成判据：必须产出 openspec_sync_ref，并满足“OpenSpec 同步记录已生成且符合 schema”。
- 交接说明：交接要求：将 openspec_sync_ref 交接给 p5。
- 执行单元：`subprocess:inline-ap:construction-plane-governance:p4`。该阶段采用临时 AP 语法，映射 skill 为 `system.integration.openspec-sync`，穿透执行策略：允许（同 Actor 场景）。

### p5 verify-and-close

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：执行 registry 校验并完成 checkpoint 与开放问题对账后收口本轮。
- 输入语义：本阶段主要消费以下输入：round_id + m6_update_bundle_ref + openspec_sync_ref + round_evidence_log_ref + open_questions_ref。
- 完成标准：完成判据：必须产出 registry_verify_report_ref + round_close_summary_ref + construction_plane_delta_ref + open_questions_ref，并满足“registry 校验通过且开放问题已落实负责人”。
- 交接说明：交接要求：将 registry_verify_report_ref + round_close_summary_ref + construction_plane_delta_ref + open_questions_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:construction-plane-governance:p5`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

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
