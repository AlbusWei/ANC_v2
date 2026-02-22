# verdict-normalizer - Test Cases

## Objective Alignment

验证 AP-020 聚合规则与统一 verdict 契约一致。

## Test Cases

### TC-001: Happy Path - 全部 pass 输出 pass

- Type: Objective
- Priority: P0
- Input: objective=pass, subjective=pass, regression=pass
- Expected: `gate_decision=pass`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=pass, final_gate_verdict_ref]

### TC-002: Fail-Closed - 关键评测包缺失

- Type: Objective
- Priority: P0
- Input: 缺失 `objective_eval_ref`
- Expected: `gate_decision=fail` 且 `reasons` 含 missing package
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=fail, reasons]

### TC-003: Traceability - P0 fail 优先阻断并可追溯

- Type: Objective
- Priority: P0
- Input: regression 包含 P0 fail 证据
- Expected: `gate_decision=fail` 且 `final_gate_verdict_ref` 可达
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=fail, p0_fail, aggregation_trace_ref]

### TC-004: Fail-Closed - test_invalid 透传聚合

- Type: Objective
- Priority: P0
- Input: objective=`test_invalid`、regression=`pass`
- Expected: `gate_decision=test_invalid` 且 `reasons` 包含 `test_invalid_present`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=test_invalid, test_invalid_present]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
