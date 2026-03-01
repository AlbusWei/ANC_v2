# qa-runtime-fixture - Test Cases

## Objective Alignment

验证 M1 OpenJudge 适配链路在 objective/regression 模式可稳定输出统一 verdict。

## Test Cases

### TC-001: Objective Gate Decision Fields

- Type: Objective
- Priority: P0
- Input: fixture pass output
- Expected: output includes pass contract fields
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=pass, compile_success]

### TC-002: Evidence Traceability Fields

- Type: Objective
- Priority: P0
- Input: fixture pass output
- Expected: output includes evidence references
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [evidence_ref=, reasons=]

### TC-003: Module Marker

- Type: Objective
- Priority: P0
- Input: fixture pass output
- Expected: output includes module marker
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [module=M3]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 5
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
