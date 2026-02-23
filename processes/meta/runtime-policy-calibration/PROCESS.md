# runtime-policy-calibration - Process Guide

## Purpose

为 M1/M2 等运行参数问题提供统一后验分析与治理同步流程，避免在模块文档硬编码策略值。

## Entry Conditions

1. `issue_ref`、`current_policy_ref`、`risk_constraints_ref` 可达。
2. `runtime_evidence_refs` 非空且每项可追溯。
3. handoff 契约满足 `role-handoff-protocol` 最小字段。

## Execution Phases

1. `p1 issue-intake-and-scope-lock`（system-analyst / `sys.arch.system-feedback-digest`）
2. `p2 evidence-collection-and-baseline`（system-analyst / `sys.arch.system-feedback-digest`）
3. `p3 posterior-analysis-and-hypothesis`（system-analyst / `sys.arch.system-feedback-digest`）
4. `p4 governance-sync`（architect / `system.ops.manual-task`）
5. `p5 decision-and-rollout-plan`（admin / `system.ops.manual-task`）
6. `p6 post-rollout-observation`（bpm / `sys.arch.system-feedback-digest`）

## Rejection Rules (Fail-Closed)

1. 证据索引不可达或样本不足。
2. handoff 字段缺失或 `to_role` 不匹配。
3. 高风险策略变更缺少 admin 审批。

## Primary Evidence Bundle

- `calibration_report_ref`
- `policy_change_proposal_ref`
- `governance_sync_minutes_ref`
- `decision_record_ref`
- `rollout_observation_ref`
