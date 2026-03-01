# template-validator - Test Cases

## Objective Alignment

验证模板与契约校验链路可稳定给出 gate 结论，并在引用或字段异常时 Fail-Closed。

## Test Cases

### TC-001: Happy Path - 模板契约校验通过

- Type: Objective
- Priority: P0
- Input: 合法 `template_ref/schema_ref/target_asset_ref/validation_profile`
- Expected: 输出 `gate_decision=pass` 且 `blocking_issues=[]`
- Evaluation Method: Exact Match

### TC-002: Fail-Closed - 缺失 schema_ref

- Type: Objective
- Priority: P0
- Input: `schema_ref` 为空
- Expected: 返回码为 2，`reason_code=missing_required_fields`
- Evaluation Method: Exact Match

### TC-003: Fail-Closed - template_ref 不可达

- Type: Objective
- Priority: P0
- Input: `template_ref` 指向不存在路径
- Expected: `gate_decision=fail` 且报告中有不可达路径
- Evaluation Method: Exact Match

### TC-004: Traceability - 报告引用 schema 与资产

- Type: Objective
- Priority: P1
- Input: 标准输入 + `--report`
- Expected: 报告含 `template_ref/schema_ref/target_asset_ref` 回链
- Evaluation Method: Rule Match

### TC-005: 策略检查 - 高风险问题阻断

- Type: Objective
- Priority: P1
- Input: profile 要求阻断高风险问题
- Expected: 存在高风险问题时 `gate_decision=fail`
- Evaluation Method: Exact Match

### TC-006: 输出契约检查 - gate 字段完整

- Type: Objective
- Priority: P2
- Input: 合法输入
- Expected: 输出必须含 `validation_report_ref/gate_decision/blocking_issues`
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa, architect]
- Timeout Seconds: 600
- Retry Policy: max 1
