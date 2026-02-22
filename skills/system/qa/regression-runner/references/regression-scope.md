# Regression Scope Reference

`regression_scope` 最小格式：逗号分隔模块列表。

示例：

- `M3,M4,M5`
- `M1,M2`

回归阻断规则：

- 任一模块 P0 fail -> `release_gate_candidate=fail`
- 无 fail 且存在 hold -> `release_gate_candidate=hold`
- 其余 -> `release_gate_candidate=pass`
