# Refactor Process

> 版本: v0.1.0 | 层级: P4 | 类型: 复合流程 | process_id: refactor

## 目标

用于结构重整与技术债治理，确保重构在不变更业务目标的前提下具备可审计质量门禁与生命周期闭环。

## 连续性边界

1. refactor 默认不触发 O7 Release 义务，除非产出包含版本化发布包。
2. refactor 必须执行完整测试准备与回归验证，不得仅靠主观判断放行。
3. 生命周期治理与 registry 同步必须在验证通过后执行。

## 阶段定义

1. `refactor-objective-and-scope`（AP-001/002/003）
2. `refactor-spec-authoring`（AP-004）
3. `refactor-test-preparation`（子流程 `quality-gate-preparation`，内部覆盖 AP-005/018/019）
4. `refactor-implementation`（AP-006）
5. `refactor-gate-evaluation`（子流程 `quality-gate-evaluation`，内部覆盖 AP-007/009/020）
6. `lifecycle-gate-sync`（AP-010/011）

## 阶段到流程映射

| 阶段 | 流程映射 | 输出 |
|---|---|---|
| refactor-objective-and-scope | AP-001, AP-002, AP-003 | refactor_objective_ref + scope_baseline_ref |
| refactor-spec-authoring | AP-004 | refactor_spec_ref |
| refactor-test-preparation | 子流程 quality-gate-preparation（内部：AP-005, AP-018, AP-019） | refactor_preparation_bundle_ref |
| refactor-implementation | AP-006 | refactor_implementation_ref |
| refactor-gate-evaluation | 子流程 quality-gate-evaluation（内部：AP-007, AP-009, AP-020） | refactor_gate_decision |
| lifecycle-gate-sync | AP-010, AP-011 | lifecycle_transition_ref + registry_sync_ref |

## 输入契约

1. `objective_ref`
2. `scope_baseline_ref`
3. `tech_debt_ref`
4. `target_asset_ref`

## 输出契约

1. `refactor_delivery_bundle_ref`
2. `final_gate_verdict_ref`
3. `lifecycle_transition_ref`
4. `registry_sync_ref`

## Fail-Closed 规则

1. 范围基线缺失或目标不清晰时拒绝进入实现。
2. 回归验证失败时拒绝状态迁移。
3. registry 校验失败时拒绝关闭 refactor 任务。
4. 关键证据缺失时直接 Fail-Closed。

## 依赖流程

1. `docs/design/processes/quality-gate-preparation-process.md`
2. `docs/design/processes/quality-gate-evaluation-process.md`
