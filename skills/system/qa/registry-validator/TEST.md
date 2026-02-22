# registry-validator - Test Cases

## Objective Alignment

验证 registry 校验技能可以稳定输出门禁级 pass/fail 报告。

## Test Cases

### TC-001: Happy Path - verify 通过

- Type: Objective
- Priority: P0
- Input: 合法 registry 与 contract
- Expected: `gate_decision=pass` 且报告可追溯
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=pass, validation_report_ref]

### TC-002: Fail-Closed - verify 失败

- Type: Objective
- Priority: P0
- Input: 注入非法 registry 条目
- Expected: `gate_decision=fail`，保留 stderr/return_code
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=fail, return_code]

### TC-003: Traceability - 报告字段完整

- Type: Objective
- Priority: P0
- Input: 任一验证执行
- Expected: 输出包含 `validation_report_ref/evidence_ref/reasons[]`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [validation_report_ref, evidence_ref, reasons]

### TC-004: Fail-Closed - registry tool 不可执行

- Type: Objective
- Priority: P0
- Input: `registry_tool_ref` 指向不存在脚本
- Expected: `gate_decision=fail` 且 `reasons` 含 `exception`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=fail, exception]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa, architect]
- Timeout Seconds: 600
- Retry Policy: max 1
