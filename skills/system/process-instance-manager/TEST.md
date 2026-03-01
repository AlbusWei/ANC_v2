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

### TC-INS-006: inline_ap 映射违规拒绝

- Type: Objective
- Priority: P0
- Input: manifest phase 使用未注册 `target_id` 且 `inline_ap` 缺失/`skill_id` 无效
- Expected: Fail-Closed，并返回 `inline_ap` 映射错误
- Evaluation Method: Exact Match

### TC-INS-007: phase 分发上下文自动拼接

- Type: Objective
- Priority: P0
- Input: 启动实例时提供 `input_ref` + `requires_spec=true` phase
- Expected: 产出 `dispatch_context_ref/task_dispatch_ref/dispatch_prompt_ref`，且输入拼接顺序符合“显式输入 -> spec_ref”
- Evaluation Method: Exact Match

### TC-INS-008: 父子交接输入继承

- Type: Objective
- Priority: P1
- Input: 子实例缺显式 `input_ref`，父实例存在可用 `output_ref`
- Expected: 子实例 phase 输入自动继承父实例最近输出引用
- Evaluation Method: Exact Match
