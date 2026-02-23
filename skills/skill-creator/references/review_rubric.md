# meta-skill-creator Review Rubric

## 评审维度

1. 触发矩阵是否可执行。
2. 输入输出契约是否字段级可检查。
3. Fail-Closed 决策表是否覆盖关键风险。
4. 脚手架输出是否可直接进入 review gate。
5. 测试、registry、文档三方是否同步。
6. 别名策略是否明确并可执行。

## 判定规则

- PASS：六项全部满足，无 P0 缺陷。
- REWORK：任一项缺失或存在不可追溯路径。

## 快速检查问题

1. 是否仅允许 `meta-skill-creator` 作为调用入口？
2. `test_mount` 与 registry `tests` 是否一致？
3. 生成产物是否含 review gate 必填字段？
