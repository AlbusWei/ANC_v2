# AP-020 Gate Decision Aggregation

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.verdict-normalizer
- Input:
  - objective_eval_ref
  - subjective_eval_ref（可选）
  - regression_eval_ref
  - aggregation_rules_ref
- Output:
  - gate_decision（`pass|fail|hold|test_invalid`）
  - reasons[]
  - evidence_ref
  - final_gate_verdict_ref
- Aggregation:
  - 任一 P0 `fail` -> `fail`
  - 无 `fail` 且存在 `hold` -> `hold`
  - 其余 -> `pass`
- Fail-Closed:
  - 任一关键评测包不可解析 -> `fail`
  - 证据链缺失 -> `fail`
- Evidence:
  - final_gate_verdict_ref
  - aggregation_trace_ref
