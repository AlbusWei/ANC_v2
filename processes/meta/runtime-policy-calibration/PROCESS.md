# runtime-policy-calibration - 流程说明

## 流程定位

- 流程级别：`P5`
- 负责人：`bpm`
- 版本：`0.2.0`
- Objective 引用：`obj-runtime-policy-calibration`

## 流程目标（自然语言）

该流程负责基于运行证据进行后验分析与策略校准，形成可决策的策略变更提案与上线观测闭环。它的意义是让触发/补跑/去重策略持续学习，而不是在文档中静态硬编码。

## 协作编排原则

1. 该流程是运行策略后验学习机制，目标是持续校准触发/去重/补跑策略。
2. 分析必须基于运行证据与基线指标，不以主观经验直接改策略。
3. 策略提案需经过治理同步与审批，保证风险可控后再进入上线观察。
4. 收口必须回填观测结果，形成“分析-决策-验证”闭环。

## 阶段语义定义

### p1 issue-intake-and-scope-lock

- 执行角色：`system-analyst`
- 阶段目的：校验议题范围与契约完整性。
- 输入语义：issue_ref + handoff_ref。
- 完成标准：必须产出 scope_lock_ref，并满足“范围、目标与交接契约均已锁定”。
- 交接说明：将 scope_lock_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:runtime-policy-calibration:p1`。该阶段采用临时 AP 语法，映射 skill 为 `sys.arch.system-feedback-digest`，穿透执行策略：允许（同 Actor 场景）。

### p2 evidence-collection-and-baseline

- 执行角色：`system-analyst`
- 阶段目的：构建证据索引与基线指标。
- 输入语义：runtime_evidence_refs + risk_constraints_ref。
- 完成标准：必须产出 evidence_index_ref + baseline_ref，并满足“证据索引可访问且样本覆盖范围明确”。
- 交接说明：将 evidence_index_ref + baseline_ref 交接给 p3。
- 执行单元：`subprocess:inline-ap:runtime-policy-calibration:p2`。该阶段采用临时 AP 语法，映射 skill 为 `sys.arch.system-feedback-digest`，穿透执行策略：允许（同 Actor 场景）。

### p3 posterior-analysis-and-hypothesis

- 执行角色：`system-analyst`
- 阶段目的：生成后验摘要与策略假设。
- 输入语义：handoff_ref + evidence_index_ref。
- 完成标准：必须产出 architecture_feedback_digest_ref，并满足“摘要包含风险等级、发现项与可决策建议”。
- 交接说明：将 architecture_feedback_digest_ref 交接给 p4。
- 执行单元：`subprocess:inline-ap:runtime-policy-calibration:p3`。该阶段采用临时 AP 语法，映射 skill 为 `sys.arch.system-feedback-digest`，穿透执行策略：允许（同 Actor 场景）。

### p4 governance-sync

- 执行角色：`architect`
- 阶段目的：与 architect/admin/bpm 同步评审并记录纪要。
- 输入语义：architecture_feedback_digest_ref。
- 完成标准：必须产出 governance_sync_minutes_ref，并满足“治理同步参与方与结论可审计”。
- 交接说明：将 governance_sync_minutes_ref 交接给 p5。
- 执行单元：`subprocess:inline-ap:runtime-policy-calibration:p4`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p5 decision-and-rollout-plan

- 执行角色：`admin`
- 阶段目的：对策略提案做批准或驳回并确定上线方案。
- 输入语义：governance_sync_minutes_ref + risk_constraints_ref。
- 完成标准：必须产出 policy_change_proposal_ref + decision_record_ref，并满足“高风险变更具备明确的 admin 决策”。
- 交接说明：将 policy_change_proposal_ref + decision_record_ref 交接给 p6。
- 执行单元：`subprocess:inline-ap:runtime-policy-calibration:p5`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p6 post-rollout-observation

- 执行角色：`bpm`
- 阶段目的：记录上线观测并关闭本轮校准。
- 输入语义：decision_record_ref + current_policy_ref。
- 完成标准：必须产出 rollout_observation_ref + calibration_report_ref，并满足“观测结果已关联决策与提案引用”。
- 交接说明：将 rollout_observation_ref + calibration_report_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:runtime-policy-calibration:p6`。该阶段采用临时 AP 语法，映射 skill 为 `sys.arch.system-feedback-digest`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `p5`。
- `p5` 在 `success` 条件下流转到 `p6`。
- `p6` 在 `success` 条件下流转到 `end`。

## 协作策略（运行态）

1. 协作模式：`phase-isolated-session`。
2. 分发运行时：`openclaw-required`。
3. 会话重置策略：`per-phase-reset`。
4. 多角色评审与决策阶段必须显式交接引用（digest/minutes/decision），避免口头化传递。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
