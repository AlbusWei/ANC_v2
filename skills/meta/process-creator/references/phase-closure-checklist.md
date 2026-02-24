# process-creator phase 闭合清单

## 闭合检查

1. 每个 phase 都包含 canonical 运行字段：`phase_id/actor/target_type/target_id/requires_spec`。
2. 每个 phase 都包含协作语义字段：`phase_purpose/input_context_ref/done_definition/handoff_note`。
3. 每个 phase 的 `target_type` 必须为 `subprocess`。
4. `target_id` 要么命中 `process_registry`，要么通过 `inline_ap` 命中 `skill_registry`。
5. `requires_spec=true` 时必须包含 `spec_ref`（`repo_relative_path#anchor`）。
6. `control_flow` 必须覆盖所有 phase 且存在 `to=end` 终止路径。
7. 出现跨断点流程时必须拆分并由上级流程编排。
8. `P4` 必须声明 `collaboration_policy`；`P5/P6` 多 Actor 协作场景也必须声明。

## Fail-Closed 触发器

- 任一 phase 缺关键字段。
- target 映射不存在或 inline_ap 无效。
- `control_flow` 无终止态或存在孤立 phase。
- 出现 legacy 字段（`control`、`failure_policy`、`skill_or_process`）。
- 触发协作策略条件但缺失 `collaboration_policy` 关键字段。
