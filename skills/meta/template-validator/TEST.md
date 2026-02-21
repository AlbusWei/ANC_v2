# template-validator - Test Cases

## Objective Alignment

验证模板/契约校验可在 lifecycle 前阻断结构错误。

## Test Cases

### TC-001: 模板契约校验通过

- Type: Objective
- Priority: P0
- Input: 完整 template_ref + schema_ref + validation_profile
- Expected: gate_decision=pass 且 report 可追溯
- Evaluation Method: Exact Match

### TC-002: 缺失 schema_ref 时 Fail-Closed

- Type: Objective
- Priority: P0
- Input: schema_ref 缺失
- Expected: gate_decision=fail 且 blocking_issues 给出缺失原因
- Evaluation Method: Exact Match
