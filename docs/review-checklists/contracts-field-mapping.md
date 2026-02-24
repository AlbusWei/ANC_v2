# Contracts Field Mapping Snapshot

最后更新：2026-02-21

> 目的：记录本轮协议硬切中“旧字段 -> 新字段/移除”的裁决，作为审计与回归依据。

## 1. BPM Dispatch 映射

| 旧字段 | 新字段/策略 | 裁决 |
|---|---|---|
| `skill` | `target_type=subprocess` + `target_id=<inline_ap.ap_id>` + `inline_ap.skill_id=<skill_registry.skill_id>` | 移除旧字段 |
| `skill_or_process` | `target_type + target_id` | 移除旧字段 |
| `skill_or_subprocess` | `target_type + target_id` | 移除旧字段 |
| `input.objective_ref` | `objective_ref`（扁平化） | 扁平化 |
| `input.spec_ref` | `spec_ref`（条件必填） | 扁平化 + 门禁 |
| `input.additional/additional_context` | 无 | 移除（无双轨） |
| `evidence`（completion） | `evidence_ref` | 结构收敛 |

## 2. Completion 映射

| 旧字段 | 新字段/策略 | 裁决 |
|---|---|---|
| `self_check`（字符串/弱结构） | `self_check.decision/reason/rule_refs[]` | 强结构化 |
| `notes` | 无 | 移除 |
| `evidence.timestamp/decision/reason` | `evidence_ref` + `self_check` | 语义拆分 |

## 3. Process Manifest 映射

| 旧字段 | 新字段/策略 | 裁决 |
|---|---|---|
| `phases[].skill_or_process` | `phases[].target_type` + `phases[].target_id` | 硬切 |
| `control` | `control_flow` | 保留单轨 `control_flow` |
| `failure_policy` | `fail_policy` | 保留单轨 `fail_policy` |
| 无 `requires_spec` | `phases[].requires_spec` | 新增 |
| 无条件 `spec_ref` | `requires_spec=true` 时 `spec_ref` 必填 | 新增门禁 |

## 4. 路径策略映射

| 旧策略 | 新策略 | 裁决 |
|---|---|---|
| 绝对路径（`/Users/...`） | canonical 根相对路径（如 `docs/...`） | 全量硬切 |
| 宽松路径正则 | 禁止绝对路径与 `..` | fail-closed |

## 5. Canonical 字段字典（本轮）

1. `task_dispatch` 必填：`instance_id`, `phase_id`, `actor`, `target_type`, `target_id`, `input_ref`, `objective_ref`, `output_contract`, `lineage_ref`, `stack_depth`, `evidence_dir`
2. `task_dispatch` 条件：`parent_instance_id`（递归场景），`spec_ref`（`phase.requires_spec=true`）
3. `task_completion` 必填：`instance_id`, `phase_id`, `actor`, `lineage_ref`, `stack_depth`, `output_ref`, `self_check`, `evidence_ref`, `status`
4. `self_check` 必填：`decision`, `reason`, `rule_refs`

## 6. 裁决来源

1. SSOT：`docs/architecture/process_architecture.md`
2. Context：`docs/architecture/context_protocol.md`
3. 接口：`docs/design/interfaces/bpm-actor-protocol.md`, `docs/design/interfaces/role-handoff-protocol.md`
4. 数据模型：`docs/design/data-models/context-schemas.md`, `docs/design/data-models/process-instance-schemas.md`
5. 机器门禁：`shared/registry/registry_contract_tool.py`
