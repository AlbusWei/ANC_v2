# trigger-ingress-normalizer - Test Cases

## Objective Alignment

验证触发入口归一能力可统一多种触发类型并在字段缺失时 Fail-Closed。

## Test Cases

### TC-001: 事件触发归一成功

- Type: Objective
- Priority: P0
- Input: 完整 event payload
- Expected: 输出 `canonical_trigger_ref` 与 `trigger_id`
- Evaluation Method: Exact Match

### TC-002: 缺失必填字段拒绝

- Type: Objective
- Priority: P0
- Input: payload 缺 `entity_id`
- Expected: Fail-Closed 并记录归一失败原因
- Evaluation Method: Exact Match
