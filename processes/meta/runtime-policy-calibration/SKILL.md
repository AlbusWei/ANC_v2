---
name: "runtime-policy-calibration"
description: "Run posterior runtime policy calibration with system-analyst digest and governance decision gates"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.3.0"
---

# runtime-policy-calibration

## Objective

将运行后验证据统一收敛为策略校准提案，并在治理同步后输出可执行决策记录。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: bpm, architect, admin, system-analyst
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: issue_ref, runtime_evidence_refs, current_policy_ref, risk_constraints_ref, handoff_ref

## Output Contract

- Format: json
- Required fields: calibration_report_ref, policy_change_proposal_ref, governance_sync_minutes_ref, decision_record_ref, rollout_observation_ref, liveness_policy_ref, no_progress_window_ref, termination_rule_ref

## Runtime Rules

1. 证据样本不足时必须 Fail-Closed，不得产出策略变更结论。
2. 高风险策略变更必须经过 `admin` 审批。
3. `system-analyst` 仅输出分析与建议，不直接执行配置变更。
4. `no_progress_window_ref` 的默认最小阈值为 900 秒，低于该值必须拒绝下发。
