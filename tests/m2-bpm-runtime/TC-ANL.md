# TC-ANL-001~003

## TC-ANL-001 Handoff 接收与结构化 Digest 输出

- Input: BPM/architect 发送满足 `role-handoff-protocol` 最小字段的交接包，并提供可达证据索引 `evidence_ref`。
- Expect:
  - `system-analyst` 接收 handoff 成功（`status=completed`）。
  - 输出 `architecture_feedback_digest_ref`，包含 `summary/findings/recommendations/evidence_refs`。
  - 输出内容可追溯到输入 `instance_id` 与证据索引。

## TC-ANL-002 证据不足 Fail-Closed 拒绝路径

- Input: handoff 字段完整但 `evidence_ref` 缺失/不可达或索引证据为空。
- Expect:
  - `system-analyst` 拒绝输出结论性 digest。
  - 返回 `status=rejected`，并给出 `reason_code`、`missing_evidence_refs`、`required_actions`。
  - 拒绝记录具备可审计字段（`instance_id`、`generated_at`、`auditable_ref`）。

## TC-ANL-003 Runtime Policy Calibration 端到端成功路径

- Input: 运行级议题输入（`issue_ref/runtime_evidence_refs/current_policy_ref/risk_constraints_ref/handoff_ref`）齐全，且高风险审批已显式通过。
- Expect:
  - `runtime-policy-calibration` 执行成功（`status=ok`）。
  - 输出 `calibration_report_ref/policy_change_proposal_ref/governance_sync_minutes_ref/decision_record_ref/rollout_observation_ref/liveness_policy_ref/no_progress_window_ref/termination_rule_ref`。
  - 过程 `runtime_trace_ref` 可回放 6 phase，且包含 `architecture_feedback_digest_ref`。
