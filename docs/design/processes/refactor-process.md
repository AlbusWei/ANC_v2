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

## 协作骨架 v1（运行级）

1. 分发策略：每个 phase 由 BPM 通过 `process-instance-manager` 执行真实 `openclaw` 分发。
2. 会话策略：启用 `reset-openclaw-session`，同一 Actor 跨 phase 强制新会话，避免重构讨论被旧上下文污染。
3. 交接策略：每个 phase 输出 `dispatch_context` 与 `phase_output` 引用，下一阶段基于引用继续协作。
4. 运行边界：本轮优先验证“跨角色协作链条可运行”，深度子流程执行在后续回合逐步接线。

<!-- phase-semantics-v2:start -->
## 阶段协作语义补充（v2）

> 说明：本节用于说明每个 phase 在系统主线中的职责与协作价值，要求可直接回答“为什么由该 Actor 在该阶段执行该动作”。

| phase_id | Actor | 阶段目的 | 输入语义 | 完成标准 | 交接语义 |
|---|---|---|---|---|---|
| `p1` | `architect` | 明确重构目标与范围基线。 | objective_context_ref + tech_debt_ref | 产出 objective_ref + scope_baseline_ref，并满足：目标与非目标明确 | 将 objective_ref + scope_baseline_ref 交接给 p2 |
| `p2` | `architect` | 编写受架构约束的重构规格。 | objective_ref + scope_baseline_ref | 产出 spec_ref，并满足：规格文档明确不变量边界与回滚方案 | 将 spec_ref 交接给 p3 |
| `p3` | `qa` | 准备以回归验证为核心的测试。 | spec_ref | 产出 test_plan_ref + preparation_bundle_ref，并满足：test_plan_ref 明确关联 refactor spec | 将 test_plan_ref + preparation_bundle_ref 交接给 p4 |
| `p4` | `kernel-dev` | 执行结构性重构改动。 | spec_ref + test_plan_ref | 产出 implementation_ref + candidate_artifacts_ref，并满足：实现与规格及约束保持关联 | 将 implementation_ref + candidate_artifacts_ref 交接给 p5 |
| `p5` | `qa` | 执行目标与回归门禁检查。 | candidate_artifacts_ref | 产出 final_gate_verdict_ref，并满足：回归结果明确且证据完整 | 将 final_gate_verdict_ref 交接给 p6 |
| `p6` | `admin` | 校验生命周期与 registry 同步包。 | final_gate_verdict_ref | 产出 lifecycle_transition_ref + registry_sync_ref，并满足：registry 同步载荷与生命周期证据完整 | 将 lifecycle_transition_ref + registry_sync_ref 交接给 initiator |
<!-- phase-semantics-v2:end -->
