# manual-task - Test Cases

## Objective Alignment

验证 manual-task 作为 BPM 通用执行入口，能按自然语言分发上下文完成任务并沉淀 `task_completion` 协议证据。

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

### TC-004: Dispatch 模式自动补全 completion

- Type: Objective
- Priority: P0
- Input: `task_dispatch` 完整，未显式提供 `completion_ref`
- Expected: 自动生成 `completion_ref`，并写入 `task_completion` 结构
- Evaluation Method: Exact Match

### TC-005: Dispatch 缺 session_id 触发拒绝

- Type: Objective
- Priority: P0
- Input: `task_dispatch.session_binding` 缺 `session_id`
- Expected: Fail-Closed，拒绝执行
- Evaluation Method: Exact Match
