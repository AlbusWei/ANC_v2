# process-creator - Test Cases

## Objective Alignment

验证流程创建输出满足 process definition standard。

## Test Cases

### TC-001: 生成可校验 process.json

- Type: Objective
- Priority: P0
- Input: 完整 process_id + phases + control_flow + fail_policy
- Expected: process.json 字段完整并可通过 contract verify
- Evaluation Method: Human Review

### TC-002: phase 未闭合时 Fail-Closed

- Type: Objective
- Priority: P0
- Input: phase 缺 target_id
- Expected: 阻断生成并返回 phase 闭合错误
- Evaluation Method: Exact Match
