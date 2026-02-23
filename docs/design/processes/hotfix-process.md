# Hotfix Process

> 版本: v0.3.0 | 层级: P4 | 类型: 复合流程 | process_id: hotfix | process_type: dev.hotfix

## 目标

用于 P0/P1 线上问题的快速修复流程，确保在压缩路径下仍满足门禁、生命周期治理与可回滚要求。

## 连续性边界

1. hotfix 允许压缩分析与设计阶段，但不允许跳过 Objective、Test、Verify。
2. 开发断点前后仍采用“准备流程 + 实现 + 评测流程”分段。
3. release 仅在 lifecycle 与 registry 证据齐备后执行。

## 阶段定义

1. `hotfix-intake`（子流程 `hotfix-intake-normalization`）
2. `scope-and-spec-fast-baseline`（子流程 `hotfix-scope-spec-baseline`）
3. `fast-test-preparation`（子流程 `quality-gate-preparation`）
4. `hotfix-implementation`（子流程 `implementation-execution-core`）
5. `hotfix-gate-evaluation`（子流程 `quality-gate-evaluation`）
6. `lifecycle-gate-sync`（子流程 `lifecycle-review`）
7. `release-packaging`（子流程 `release-packaging-governed`）

## 阶段到流程映射

| 阶段 | 流程映射 | 输出 |
|---|---|---|
| hotfix-intake | `hotfix-intake-normalization` | `hotfix_objective_ref` + `impact_scope_ref` + `rollback_direction_ref` |
| scope-and-spec-fast-baseline | `hotfix-scope-spec-baseline` | `hotfix_scope_baseline_ref` + `spec_ref` |
| fast-test-preparation | `quality-gate-preparation` | `test_plan_ref` + `hotfix_preparation_bundle_ref` |
| hotfix-implementation | `implementation-execution-core` | `implementation_ref` + `candidate_artifacts_ref` |
| hotfix-gate-evaluation | `quality-gate-evaluation` | `final_gate_verdict_ref` |
| lifecycle-gate-sync | `lifecycle-review` | `lifecycle_transition_ref` + `registry_sync_ref` |
| release-packaging | `release-packaging-governed` | `release_package_ref` + `rollback_bundle_ref` |

## phase 目标态映射

| phase_id | 阶段 | target_type | target_id |
|---|---|---|---|
| p1 | hotfix-intake | subprocess | hotfix-intake-normalization |
| p2 | scope-and-spec-fast-baseline | subprocess | hotfix-scope-spec-baseline |
| p3 | fast-test-preparation | subprocess | quality-gate-preparation |
| p4 | hotfix-implementation | subprocess | implementation-execution-core |
| p5 | hotfix-gate-evaluation | subprocess | quality-gate-evaluation |
| p6 | lifecycle-gate-sync | subprocess | lifecycle-review |
| p7 | release-packaging | subprocess | release-packaging-governed |

## I/O 闭合策略

1. `test_plan_ref`：`p3` 显式产出并作为 `p4` 必填输入。
2. `candidate_artifacts_ref`：`p4` 明确声明从 `implementation_ref` 映射生成。
3. 发布输入闭合：`p7` 必须同时消费 `candidate_artifacts_ref`、`final_gate_verdict_ref`、`lifecycle_transition_ref`、`registry_sync_ref`。

## 输入契约

1. `incident_context_ref`
2. `target_asset_ref`

## 输出契约

1. `final_gate_verdict_ref`
2. `lifecycle_transition_ref`
3. `registry_sync_ref`
4. `release_package_ref`
5. `rollback_bundle_ref`

## Fail-Closed 规则

1. 无 incident 输入或回滚方向时拒绝进入实现。
2. hotfix 回归验证失败时禁止发布。
3. lifecycle/registry 校验失败时禁止状态迁移。
4. 关键证据缺失时升级 `actor -> owner -> bpm -> admin -> human`。
