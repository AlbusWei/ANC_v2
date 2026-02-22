# evidence-archiver - Test Cases

## Objective Alignment

验证证据归档技能可产出可审计、可追溯的 M1 证据包。

## Test Cases

### TC-001: Happy Path - 归档成功

- Type: Objective
- Priority: P0
- Input: 合法 run_id/profile_id/gate_decision
- Expected: 产出 `index.json`、`unified_verdict.json`、archive report
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [evidence_index_ref, archive_report_ref, gate_decision]

### TC-002: Fail-Closed - 非法 gate_decision

- Type: Objective
- Priority: P0
- Input: `gate_decision=unknown`
- Expected: `gate_decision=fail` 且给出 invalid decision 原因
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=fail, invalid_gate_decision]

### TC-003: Traceability - 索引字段完整

- Type: Objective
- Priority: P0
- Input: 合法归档输入
- Expected: index 含 `run_id/profile_id/input_refs/raw_eval_ref/gate_decision/reasons/actor/timestamps`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [run_id, profile_id, input_refs, raw_eval_ref, gate_decision, actor, timestamps]

### TC-004: Fail-Closed - 缺失 traceability 输入

- Type: Objective
- Priority: P0
- Input: 不传 `input_refs` 且不传 `raw_eval_ref`
- Expected: `gate_decision=fail` 且 reasons 包含 `missing_traceability_inputs`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=fail, missing_traceability_inputs]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa, bpm]
- Timeout Seconds: 600
- Retry Policy: max 1
