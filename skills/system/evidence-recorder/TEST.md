# evidence-recorder - Test Cases

## Objective Alignment

验证触发运行时证据在命中/拒绝场景下均可双向追溯。

## Test Cases

### TC-001: 命中触发证据归档成功

- Type: Objective
- Priority: P0
- Input: 合法 `trigger_id + instance_id + decision=hit`
- Expected: 输出 `trigger_receipt_ref/evidence_index_ref/traceability_link_ref`
- Evaluation Method: Exact Match

### TC-002: 缺失实例标识拒绝归档

- Type: Objective
- Priority: P0
- Input: 缺失 `instance_id`
- Expected: Fail-Closed 并写入错误证据
- Evaluation Method: Exact Match
