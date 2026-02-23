# meta-skill-creator 执行清单

## 输入检查

1. `skill_name/layer/namespace/objective_ref` 是否完整。
2. 命名是否满足 kebab-case 与语义约束。
3. 目标范围是否包含 Fail-Closed 边界。

## 输出检查

1. `SKILL.md` frontmatter 可解析。
2. Capability Contract YAML 字段完整。
3. `TEST.md` 至少含 2 个 Fail-Closed 与 1 个 Traceability 用例。
4. registry patch 计划包含 `name/version/status/tests`。
5. `test_mount` 与 registry `tests.test_doc` 对齐。

## 生命周期检查

1. `draft -> review`：契约完整 + registry verify 通过。
2. `review -> active`：运行级 smoke 与回归证据齐全。

## 失败模式

- `missing_required_fields`
- `invalid_naming`
- `contract_incomplete`
- `registry_not_synced`
- `review_gate_failed`
