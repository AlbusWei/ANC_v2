# release-packaging-governed - Test Plan

## 覆盖目标

1. 产出发布包、changelog、发布决策、回滚包。
2. gate 证据缺失时 Fail-Closed。
3. lifecycle/registry 证据缺失时 Fail-Closed。

## 最小用例

1. TC-RPG-001: Happy path。
2. TC-RPG-002: gate verdict 缺失。
3. TC-RPG-003: registry sync 缺失。
