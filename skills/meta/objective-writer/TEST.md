# objective-writer - Test Cases

## Objective Alignment

验证 objective 输出可被 Spec/Test 阶段直接复用，且边界清晰。

## Test Cases

### TC-001: 产出可测目标

- Type: Objective
- Priority: P0
- Input: 完整 objective_context + success_criteria
- Expected: 输出包含可测成功标准和非目标边界
- Evaluation Method: Human Review

### TC-002: 缺失成功标准时 Fail-Closed

- Type: Objective
- Priority: P0
- Input: 缺失 success_criteria
- Expected: 拒绝产出并返回缺失字段
- Evaluation Method: Exact Match
