# AP-025 Hold Resolution and Escalation

> 版本: v0.2.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: sys.bpm.escalation-handler
- Input:
  - hold_case_ref
  - triage_action
  - health_maintenance_ref
  - termination_rule_ref
- Output:
  - hold_resolution_ref
  - escalation_ref（可选）
  - external_gate_decision（`fail`）
- Escalation chain:
  - `qa -> bpm -> admin`
- Fail-Closed:
  - 闭环决策缺失 -> `fail`
  - 升级链不完整或越级 -> `fail`
  - 存在未收敛 hold 但输出非 `fail` 对外门禁结论 -> `fail`
- Evidence:
  - hold_resolution_ref
  - escalation_ref
