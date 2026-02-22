# process-instance-manager - Test Cases

## Objective Alignment

验证 BPM 在实例创建、状态推进、递归隔离与流程闭合校验场景下满足 Fail-Closed 与证据可追溯要求。

## Test Cases

### TC-INS-001: 创建根实例并写入状态证据

- Type: Objective
- Priority: P0
- Input: 合法 `process_id + phase_id + stack_depth=0`
- Expected: 产出 `instance_id/runtime_state/state_transition_ref/evidence_ref`，且写入 `session_binding.json`
- Evaluation Method: Exact Match

### TC-INS-002: 子实例深度与会话隔离

- Type: Objective
- Priority: P0
- Input: 合法 `parent_instance_id` 子调用
- Expected: `stack_depth = parent + 1`，且子实例 `session_id != parent_session_id`
- Evaluation Method: Exact Match

### TC-INS-003: 禁止复用父会话

- Type: Objective
- Priority: P0
- Input: 子实例显式传入与父实例相同 `session_id`
- Expected: Fail-Closed
- Evaluation Method: Exact Match

### TC-INS-004: OpenClaw 显式会话调度

- Type: Objective
- Priority: P0
- Input: 任意合法实例启动
- Expected: 调度命令显式包含 `--session-id`
- Evaluation Method: Exact Match

### TC-INS-005: 历史迁移与回放验证

- Type: Objective
- Priority: P0
- Input: `agents/control/BPM/memory/process_instances/` 全量实例
- Expected: 迁移报告失败数为 0，回放报告失败数为 0
- Evaluation Method: Exact Match

### Legacy TC-003: 流程闭合校验失败直接拒绝

- Type: Objective
- Priority: P0
- Input: manifest 中存在未映射 phase 或非法 control_flow
- Expected: Fail-Closed 并产出解析失败证据
- Evaluation Method: Exact Match
