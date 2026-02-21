# evaluation-runner - Test Cases

## Objective Alignment

验证统一评测入口在三类评测模式下输出可解析 verdict 与证据包。

## Test Cases

### TC-001: objective 模式执行成功

- Type: Objective
- Priority: P0
- Input: 合法 `preparation_bundle_ref` + `actual_output_refs`
- Expected: 返回 `evaluation_verdict` 与 `raw_eval_ref`
- Evaluation Method: Exact Match

### TC-002: 无效模式 fail-closed

- Type: Objective
- Priority: P0
- Input: `evaluation_mode=unknown`
- Expected: `evaluation_verdict=fail` 并记录 runner 错误
- Evaluation Method: Exact Match
