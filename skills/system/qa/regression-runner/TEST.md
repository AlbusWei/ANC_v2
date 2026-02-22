# regression-runner - Test Cases

## Objective Alignment

验证跨模块回归评测的编排、阻断与证据输出能力。

## Test Cases

### TC-001: Happy Path - 跨模块回归通过

- Type: Objective
- Priority: P0
- Input: M3/M4/M5 回归结果均 pass
- Expected: `release_gate_candidate=pass`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [release_gate_candidate=pass, regression_eval_ref, regression_report_ref]

### TC-002: Fail-Closed - 关键输入缺失阻断

- Type: Objective
- Priority: P0
- Input: 缺失 `preparation_bundle_ref` 或 `actual_output_refs`
- Expected: `release_gate_candidate=fail` 且给出缺失原因
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [release_gate_candidate=fail, missing_actual_output]

### TC-003: Traceability - 回归报告可追溯

- Type: Objective
- Priority: P0
- Input: 合法 scope + 输出
- Expected: `regression_eval_ref/regression_report_ref/evidence_ref` 可追溯
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [regression_eval_ref, regression_report_ref, evidence_ref]

### TC-004: Fail-Closed - 输出映射歧义阻断

- Type: Objective
- Priority: P0
- Input: `regression_scope=M3,M4,M5` 但仅传 2 个 `actual_output_refs`
- Expected: `release_gate_candidate=fail` 且 reasons 包含 `ambiguous_actual_output_mapping`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [release_gate_candidate=fail, ambiguous_actual_output_mapping]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
