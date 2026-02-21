# Hotfix Process

> 版本: v0.1.0 | 层级: P4 | 类型: 复合流程 | process_id: hotfix

## 目标

用于 P0/P1 线上问题的快速修复流程，保证紧急修复在缩短路径下仍满足门禁与生命周期治理。

## 连续性边界

1. hotfix 允许压缩分析与设计阶段，但不允许跳过 Objective、Test、Verify。
2. 开发断点前后仍采用“准备流程 + 实现 + 评测流程”分段。
3. release 仅在 lifecycle 与 registry 证据齐备后执行。

## 阶段定义

1. `hotfix-intake`（AP-001/002）
2. `scope-and-spec-fast-baseline`（AP-003/004）
3. `fast-test-preparation`（AP-005/018/019）
4. `hotfix-implementation`（AP-006）
5. `hotfix-gate-evaluation`（AP-007/009/020）
6. `lifecycle-gate-sync`（AP-010/011）
7. `release-packaging`（AP-012）

## 阶段到原子流程映射

| 阶段 | 原子流程 | 输出 |
|---|---|---|
| hotfix-intake | AP-001, AP-002 | hotfix_objective_ref |
| scope-and-spec-fast-baseline | AP-003, AP-004 | hotfix_spec_ref |
| fast-test-preparation | AP-005, AP-018, AP-019 | hotfix_preparation_bundle_ref |
| hotfix-implementation | AP-006 | hotfix_implementation_ref |
| hotfix-gate-evaluation | AP-007, AP-009, AP-020 | hotfix_gate_decision |
| lifecycle-gate-sync | AP-010, AP-011 | lifecycle_transition_ref + registry_sync_ref |
| release-packaging | AP-012 | hotfix_release_package_ref |

## 输入契约

1. `incident_ref`
2. `objective_ref`
3. `impact_scope`
4. `rollback_plan`
5. `target_asset_ref`

## 输出契约

1. `hotfix_delivery_bundle_ref`
2. `final_gate_verdict_ref`
3. `lifecycle_transition_ref`
4. `hotfix_release_package_ref`

## Fail-Closed 规则

1. 无 `incident_ref` 或回滚计划时拒绝进入实现。
2. hotfix 回归验证失败时禁止发布。
3. lifecycle/registry 校验失败时禁止状态迁移。
4. 关键证据缺失时升级 `actor -> owner -> bpm -> admin -> human`。

## 依赖流程

1. `docs/design/processes/quality-gate-preparation-process.md`
2. `docs/design/processes/quality-gate-evaluation-process.md`
3. `docs/design/processes/hold-governance-process.md`
