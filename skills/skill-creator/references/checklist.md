# skill-creator Checklist

## 输入检查

- skill 名称、目标与边界明确。
- 至少定义 1 个 happy path + 1 个 fail-closed path + 1 个 traceability path。
- 约束包含权限、成本或安全边界。

## 输出检查

- `SKILL.md` frontmatter 可解析（`name/description/license/compatibility`）。
- `SKILL.md` 包含 `Capability Contract (Machine-Readable)` YAML 且可解析。
- `TEST.md` 已创建并含 P0 用例。
- registry 条目字段完整且路径可达。
- `test_mount` 与 registry `tests` 字段一致。
- review/smoke evidence 已落盘。

## 生命周期检查

- `draft -> review`：契约完整 + verify 通过。
- `review -> active`：smoke 通过 + evidence 可追溯。

## 失败模式

- `frontmatter_invalid`
- `capability_contract_invalid`
- `missing_test_asset`
- `registry_not_synced`
- `missing_lifecycle_evidence`
