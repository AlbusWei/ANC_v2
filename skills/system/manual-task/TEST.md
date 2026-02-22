# manual-task - Test Cases

## Objective Alignment

验证人工任务 fallback 在 Fail-Closed 约束下可产出结构化证据。

## Test Cases

### TC-001: 结构化输出完整

- Type: Objective
- Priority: P0
- Input: 提供完整 `objective_ref/task_ref/acceptance_criteria`
- Expected: 输出含 `output_ref/evidence_ref/decision/reason`
- Evaluation Method: Exact Match

### TC-002: 输入缺失触发拒绝

- Type: Objective
- Priority: P0
- Input: 缺失 `task_ref`
- Expected: 返回失败并说明缺失字段
- Evaluation Method: Exact Match

### TC-003: 缺失 expected_outputs 触发拒绝

- Type: Objective
- Priority: P0
- Input: 缺失 `expected_outputs`
- Expected: Fail-Closed，并拒绝产出无证据回合结果
- Evaluation Method: Exact Match
