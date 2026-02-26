# Runtime Policy Calibration Process

> 版本: v1.1.0 | 层级: P5 | 类型: 治理复合流程 | process_id: runtime-policy-calibration | 生命周期: review

## 目标

统一承接“必须通过运行后验分析才能给出实证结论”的治理问题，避免在模块文档中直接硬编码参数。

典型议题：

1. M1 测试执行时长估计、`no_progress_window` 与门禁参数校准。
2. M2 `catchup_policy_ref` 动态窗口校准与 `time_bucket_strategy` 调参。
3. 其它依赖运营分析才能确定的阈值、窗口、采样策略。

## 连续性边界

1. 本流程属于治理分析与决策同步段，不承担业务交付执行。
2. 本流程输出“策略更新提案 + 决策记录”，由下游执行流程按决策实施。

## 阶段定义

1. `issue-intake-and-scope-lock`
2. `evidence-collection-and-baseline`
3. `posterior-analysis-and-hypothesis`
4. `governance-sync`
5. `decision-and-rollout-plan`
6. `post-rollout-observation`

## 角色分工

1. `kernel/system-analyst`：主责证据采集、后验分析与假设提案。
2. `architect`：评估架构一致性与策略变更影响。
3. `admin`：审批高风险策略变更与执行权限边界。
4. `bpm`：接收决策并回写到流程策略配置。

## 输入契约

1. `issue_ref`
2. `runtime_evidence_refs`
3. `current_policy_ref`
4. `risk_constraints_ref`
5. `handoff_ref`

## 输出契约

1. `calibration_report_ref`
2. `policy_change_proposal_ref`
3. `governance_sync_minutes_ref`
4. `decision_record_ref`
5. `rollout_observation_ref`
6. `liveness_policy_ref`
7. `no_progress_window_ref`
8. `termination_rule_ref`

## Fail-Closed

1. 证据样本不足且无法补证，不得输出参数更新结论。
2. 未完成 `system-analyst -> architect/admin/bpm` 同步，不得推进策略更新。
3. 高风险策略变更未经 admin 确认，不得下发执行。
4. 未显式给出 `no_progress_window_ref` 或其窗口阈值小于 `900s`，不得下发执行。

## 运行入口

1. Process 资产：`processes/meta/runtime-policy-calibration/process.json`
2. Runner：`processes/meta/runtime-policy-calibration/scripts/runtime_policy_calibration_runner.py`
3. 核心技能：`skills/system/system-feedback-digest/scripts/system_feedback_digest_runner.py`

## 测试挂载

1. 用例文档：`tests/m2-bpm-runtime/TC-ANL.md`
2. 回归入口：`tests/m2-bpm-runtime/run_tc_anl.py`
3. 生产证据：`runtime_data/execution/evidence/bpm-runtime/w5_system_analyst_prod_cases/`

## 证据要求

1. 必须保留采样区间、样本量、分位统计、异常样本说明。
2. 必须保留“旧策略 -> 新策略”差异与回滚条件。
3. 必须保留 post-rollout 观测结果用于下一轮校准。
4. 必须保留 `liveness_policy_ref/no_progress_window_ref/termination_rule_ref` 的版本化引用与生效时间。

<!-- phase-semantics-v2:start -->
## 阶段协作语义补充（v2）

> 说明：本节用于说明每个 phase 在系统主线中的职责与协作价值，要求可直接回答“为什么由该 Actor 在该阶段执行该动作”。

| phase_id | Actor | 阶段目的 | 输入语义 | 完成标准 | 交接语义 |
|---|---|---|---|---|---|
| `p1` | `system-analyst` | 校验议题范围与契约完整性。 | issue_ref + handoff_ref | 产出 scope_lock_ref，并满足：范围、目标与交接契约均已锁定 | 将 scope_lock_ref 交接给 p2 |
| `p2` | `system-analyst` | 构建证据索引与基线指标。 | runtime_evidence_refs + risk_constraints_ref | 产出 evidence_index_ref + baseline_ref，并满足：证据索引可访问且样本覆盖范围明确 | 将 evidence_index_ref + baseline_ref 交接给 p3 |
| `p3` | `system-analyst` | 生成后验摘要与策略假设。 | handoff_ref + evidence_index_ref | 产出 architecture_feedback_digest_ref，并满足：摘要包含风险等级、发现项与可决策建议 | 将 architecture_feedback_digest_ref 交接给 p4 |
| `p4` | `architect` | 与 architect/admin/bpm 同步评审并记录纪要。 | architecture_feedback_digest_ref | 产出 governance_sync_minutes_ref，并满足：治理同步参与方与结论可审计 | 将 governance_sync_minutes_ref 交接给 p5 |
| `p5` | `admin` | 对策略提案做批准或驳回并确定上线方案。 | governance_sync_minutes_ref + risk_constraints_ref | 产出 policy_change_proposal_ref + decision_record_ref + liveness_policy_ref + no_progress_window_ref + termination_rule_ref，并满足：高风险变更具备明确的 admin 决策 | 将 policy_change_proposal_ref + decision_record_ref + liveness_policy_ref + no_progress_window_ref + termination_rule_ref 交接给 p6 |
| `p6` | `bpm` | 记录上线观测并关闭本轮校准。 | decision_record_ref + current_policy_ref + liveness_policy_ref + no_progress_window_ref + termination_rule_ref | 产出 rollout_observation_ref + calibration_report_ref，并满足：观测结果已关联决策与提案引用 | 将 rollout_observation_ref + calibration_report_ref 交接给 initiator |
<!-- phase-semantics-v2:end -->
