# objective-scope-baseline - Test Plan

## 覆盖目标

1. 主链路：输入 `objective_context_ref` 后产出 `objective_ref/scope_baseline_ref`。
2. Fail-Closed：缺失输入或冲突上下文时拒绝推进。
3. 可追溯：阶段输出与证据字段可回放。

## 最小用例

1. TC-OSB-001: Happy path。
2. TC-OSB-002: 缺失 `objective_context_ref`。
3. TC-OSB-003: 上下文冲突导致阻断。
