# hotfix-intake-normalization - Test Plan

## 覆盖目标

1. 产出 `hotfix_objective_ref/impact_scope_ref/rollback_direction_ref`。
2. 缺 incident 输入时 Fail-Closed。
3. rollback 方向缺失时阻断。

## 最小用例

1. TC-HIN-001: Happy path。
2. TC-HIN-002: incident 缺失。
3. TC-HIN-003: rollback 方向不可判定。
