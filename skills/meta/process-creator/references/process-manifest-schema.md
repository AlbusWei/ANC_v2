# process-creator manifest 字段清单

## process.json 最小必填字段

1. `process_id`
2. `process_level`
3. `owner`
4. `phases`
5. `control_flow`
6. `fail_policy`
7. `lineage_policy`

## phase 子字段要求

| 字段 | 必填 | 说明 |
|---|---|---|
| `phase_id` | 是 | phase 稳定标识 |
| `target_type` | 是 | `atomic_process` 或 `subprocess` |
| `target_id` | 是 | AP 或子流程 ID |
| `requires_spec` | 是 | 是否强制引用 spec |
| `spec_ref` | 条件 | 当 `requires_spec=true` 时必填 |

## 兼容性

- 与 `docs/design/standards/process-definition-standard.md` 对齐。
