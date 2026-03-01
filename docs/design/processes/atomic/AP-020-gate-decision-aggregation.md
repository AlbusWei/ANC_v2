# AP-020 Gate Decision Aggregation

> 版本: v0.3.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.verdict-normalizer
- Input:
  - objective_eval_ref
  - subjective_eval_ref（可选）
  - regression_eval_ref
  - aggregation_rules_ref
- Output:
  - gate_decision（`pass|fail|test_invalid`）
  - runtime_gate_state（`pass|fail|hold|test_invalid`）
  - reasons[]
  - evidence_ref
  - final_gate_verdict_ref
- Aggregation:
  - 任一 P0 `fail` -> `gate_decision=fail` 且 `runtime_gate_state=fail`
  - 无 `fail` 且存在 `hold` -> `gate_decision=fail` 且 `runtime_gate_state=hold`
  - 其余 -> `gate_decision=pass` 且 `runtime_gate_state=pass`
- Fail-Closed:
  - 任一关键评测包不可解析 -> `fail`
  - 证据链缺失 -> `fail`
- Governance:
  - 当 `runtime_gate_state=hold` 时必须路由 `hold-governance`，并记录 `hold_case_ref`
  - `hold` 不得作为对外门禁结论返回发布链路
  - 当 `hold-governance.retest_recommendation=auto-retest` 且回测预算未耗尽时，允许自动回路重跑评测链路
- Evidence:
  - final_gate_verdict_ref
  - aggregation_trace_ref
