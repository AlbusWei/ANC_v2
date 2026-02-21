# skill-creator Checklist

## 输入检查

- skill 名称、目标与边界明确。
- 触发场景至少一个正常场景与一个失败场景。
- 约束包含权限、成本或安全边界。

## 输出检查

- `SKILL.md` frontmatter 可解析。
- `SKILL.md` 包含 `Capability Contract (Machine-Readable)` YAML 块且可解析。
- `tests/<skill-name>/TEST.md` 已创建。
- registry 条目字段完整且路径可达。
- `test_mount` 与 registry `tests` 字段一致。

## 失败模式

- `frontmatter_invalid`
- `capability_contract_invalid`
- `missing_test_asset`
- `registry_not_synced`

## 通过标准

- 资产结构完整。
- 契约字段完整。
- 路径全部可追溯。
