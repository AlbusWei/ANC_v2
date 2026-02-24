# process-creator manifest 字段清单

## process.json 最小必填字段

1. `process_id`
2. `version`
3. `process_level`
4. `phases`
5. `control_flow`
6. `fail_policy`
7. `evidence_policy`
8. `lineage_policy`

> `collaboration_policy` 为分层条件字段：`P4` 强制；`P5/P6` 在“强协作（多 Actor）”场景强制。

## phase 子字段要求

| 字段 | 必填 | 说明 |
|---|---|---|
| `phase_id` | 是 | phase 稳定标识 |
| `name` | 是 | 阶段名称 |
| `actor` | 是 | 执行角色 |
| `target_type` | 是 | 固定为 `subprocess` |
| `target_id` | 是 | 子流程 ID 或临时 AP ID |
| `requires_spec` | 是 | 是否强制引用 spec |
| `spec_ref` | 条件 | 当 `requires_spec=true` 时必填 (`repo_relative_path#anchor`) |
| `phase_purpose` | 是 | 阶段目的 |
| `input_context_ref` | 是 | 输入语义引用 |
| `done_definition` | 是 | 完成标准 |
| `handoff_note` | 是 | 交接说明 |

## inline_ap 规则

1. 当 `target_id` 未命中 `process_registry.process_id` 时必须提供 `inline_ap`。
2. `inline_ap` 必填：`ap_id/skill_id/actor/pierce_allowed`。
3. `inline_ap.ap_id` 必须等于 `target_id`。
4. `inline_ap.skill_id` 必须命中 `skill_registry.skill_id`。
5. 当 `pierce_allowed=true` 时，`inline_ap.actor` 必须等于 `phase.actor`。

## collaboration_policy 规则

1. `P4` 流程必须声明 `collaboration_policy`。
2. `P5/P6` 若为多 Actor 协作流程，必须声明 `collaboration_policy`。
3. `collaboration_policy` 最小字段：`mode`、`dispatch_runtime`、`session_reset`。
4. 单 Actor 的 `P5/P6` 可不声明 `collaboration_policy`，但建议在跨会话协作时显式声明。

## 兼容性

- 与 `docs/design/standards/process-definition-standard.md` 对齐。
- 与 `docs/architecture/process_architecture.md` 的 BPM canonical schema 对齐。
