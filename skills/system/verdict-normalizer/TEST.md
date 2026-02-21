# verdict-normalizer - Test Cases

## Objective Alignment

验证门禁聚合符合统一 verdict 契约与 P0 优先阻断规则。

## Test Cases

### TC-001: P0 fail 优先

- Type: Objective
- Priority: P0
- Input: objective 或 regression 含 P0 fail
- Expected: `gate_decision=fail`
- Evaluation Method: Rule Match

### TC-002: 无 fail 且存在 hold

- Type: Objective
- Priority: P0
- Input: objective=pass, regression=hold
- Expected: `gate_decision=hold`
- Evaluation Method: Rule Match
