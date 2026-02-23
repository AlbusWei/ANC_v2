# process-creator phase 闭合清单

## 闭合检查

1. 每个 phase 有明确 `target_type/target_id`。
2. 每个 phase 可映射到已定义 AP 或子流程。
3. 不跨非连续生命周期段。
4. 跨断点必须拆分并由上级编排。
5. `requires_spec=true` 时存在 `spec_ref`。

## Fail-Closed 触发器

- 任一 phase 缺关键字段。
- 出现无映射 phase。
- 出现跨断点未拆分的流程段。
