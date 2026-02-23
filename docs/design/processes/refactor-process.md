# Refactor Process

> 版本: v0.3.0 | 层级: P4 | 类型: 复合流程 | process_id: refactor | process_type: dev.refactor

## 目标

用于结构重整与技术债治理，确保重构在不变更业务目标的前提下具备可审计质量门禁与生命周期闭环。

## 连续性边界

1. refactor 默认不触发 Release 义务，除非产出包含版本化发布包。
2. 必须执行完整测试准备与回归验证，不得仅靠主观判断放行。
3. 生命周期治理与 registry 同步必须在验证通过后执行。

## 阶段定义

1. `refactor-objective-and-scope`（子流程 `objective-scope-baseline`）
2. `refactor-spec-authoring`（子流程 `spec-authoring-contract`）
3. `refactor-test-preparation`（子流程 `quality-gate-preparation`）
4. `refactor-implementation`（子流程 `implementation-execution-core`）
5. `refactor-gate-evaluation`（子流程 `quality-gate-evaluation`）
6. `lifecycle-gate-sync`（子流程 `lifecycle-review`）

## 阶段到流程映射

| 阶段 | 流程映射 | 输出 |
|---|---|---|
| refactor-objective-and-scope | `objective-scope-baseline` | `objective_ref` + `scope_baseline_ref` |
| refactor-spec-authoring | `spec-authoring-contract` | `spec_ref` |
| refactor-test-preparation | `quality-gate-preparation` | `test_plan_ref` + `refactor_preparation_bundle_ref` |
| refactor-implementation | `implementation-execution-core` | `implementation_ref` + `candidate_artifacts_ref` |
| refactor-gate-evaluation | `quality-gate-evaluation` | `final_gate_verdict_ref` |
| lifecycle-gate-sync | `lifecycle-review` | `lifecycle_transition_ref` + `registry_sync_ref` |

## phase 目标态映射

| phase_id | 阶段 | target_type | target_id |
|---|---|---|---|
| p1 | refactor-objective-and-scope | subprocess | objective-scope-baseline |
| p2 | refactor-spec-authoring | subprocess | spec-authoring-contract |
| p3 | refactor-test-preparation | subprocess | quality-gate-preparation |
| p4 | refactor-implementation | subprocess | implementation-execution-core |
| p5 | refactor-gate-evaluation | subprocess | quality-gate-evaluation |
| p6 | lifecycle-gate-sync | subprocess | lifecycle-review |

## I/O 闭合策略

1. `test_plan_ref`：在 `p3 -> p4` 链路中显式闭合。
2. `candidate_artifacts_ref`：在 `p4` 明确由 `implementation_ref` 映射生成。
3. `lifecycle_transition_ref/registry_sync_ref`：由 `p6` 成对产出并作为收口证据。

## 输入契约

1. `objective_context_ref`
2. `tech_debt_ref`
3. `target_asset_ref`

## 输出契约

1. `final_gate_verdict_ref`
2. `lifecycle_transition_ref`
3. `registry_sync_ref`

## Fail-Closed 规则

1. 范围基线缺失或目标不清晰时拒绝进入实现。
2. 回归验证失败时拒绝状态迁移。
3. registry 校验失败时拒绝关闭 refactor 任务。
4. 关键证据缺失时直接 Fail-Closed。
