# Full Development Process

> 版本: v0.4.0 | 层级: P4 | 类型: 复合流程 | process_id: full-development | process_type: dev.internal-productization

## 目标

用于内部系统资产（Agent/Skill/Process）的全链路开发闭环，覆盖 Objective 到 lifecycle/release/evolution 的标准路径。

## 连续性边界

1. 通过“开发前准备 -> 实现断点 -> 开发后评测 -> 生命周期治理 -> 发布与演化”分段编排满足连续性约束。
2. `quality-gate-preparation` 与 `quality-gate-evaluation` 由上级流程跨断点编排，不在同一子流程硬拼。
3. lifecycle 与 release 前置证据必须来自已通过的 gate 结果，缺失时默认 Fail-Closed。

## 阶段定义

1. `objective-intake-and-scope`（子流程 `objective-scope-baseline`）
2. `spec-authoring`（子流程 `spec-authoring-contract`）
3. `quality-gate-preparation`（子流程 `quality-gate-preparation`）
4. `implementation-execution`（子流程 `implementation-execution-core`）
5. `quality-gate-evaluation`（子流程 `quality-gate-evaluation`）
6. `lifecycle-gate-sync`（子流程 `lifecycle-review`）
7. `release-packaging`（子流程 `release-packaging-governed`）
8. `evolution-feedback-planning`（子流程 `evolution-feedback-planning`）

## 阶段到流程映射

| 阶段 | 流程映射 | 输出 |
|---|---|---|
| objective-intake-and-scope | `objective-scope-baseline` | `objective_ref` + `scope_baseline_ref` |
| spec-authoring | `spec-authoring-contract` | `spec_ref` |
| quality-gate-preparation | `quality-gate-preparation` | `test_plan_ref` + `preparation_bundle_ref` |
| implementation-execution | `implementation-execution-core` | `implementation_ref` + `candidate_artifacts_ref` |
| quality-gate-evaluation | `quality-gate-evaluation` | `final_gate_verdict_ref` |
| lifecycle-gate-sync | `lifecycle-review` | `lifecycle_transition_ref` + `registry_sync_ref` |
| release-packaging | `release-packaging-governed` | `release_package_ref` + `rollback_bundle_ref` |
| evolution-feedback-planning | `evolution-feedback-planning` | `improvement_plan_ref` + `retro_report_ref` |

## phase 目标态映射

| phase_id | 阶段 | target_type | target_id |
|---|---|---|---|
| p1 | objective-intake-and-scope | subprocess | objective-scope-baseline |
| p2 | spec-authoring | subprocess | spec-authoring-contract |
| p3 | quality-gate-preparation | subprocess | quality-gate-preparation |
| p4 | implementation-execution | subprocess | implementation-execution-core |
| p5 | quality-gate-evaluation | subprocess | quality-gate-evaluation |
| p6 | lifecycle-gate-sync | subprocess | lifecycle-review |
| p7 | release-packaging | subprocess | release-packaging-governed |
| p8 | evolution-feedback-planning | subprocess | evolution-feedback-planning |

## I/O 闭合策略

1. `test_plan_ref`：由 `p3` 显式产出并作为 `p4` 必填输入。
2. `candidate_artifacts_ref`：在 `p4` 明确声明 `candidate_artifacts_ref <- implementation_ref` 的映射语义。
3. `feedback_evidence_ref`：由发布证据、质量门禁证据、运行反馈证据聚合后输入 `p8`。

## 输入契约

1. `objective_context_ref`
2. `input_payload`
3. `target_asset_type`（`agent|skill|process`）
4. `lifecycle_target`

## 输出契约

1. `final_gate_verdict_ref`
2. `lifecycle_transition_ref`
3. `registry_sync_ref`
4. `release_package_ref`
5. `improvement_plan_ref`
6. `retro_report_ref`

## Fail-Closed 规则

1. Objective/Spec/Test 任一证据缺失时阻断实现。
2. `quality-gate-evaluation` 非 `pass` 时阻断 lifecycle/release。
3. lifecycle 或 registry 证据缺失时阻断交付并触发升级。
4. phase 与子流程映射或 I/O 契约不闭合时拒绝流程启动。

## 协作骨架 v1（P9：full-development 先行）

1. 协作目标：让 `full-development` 先具备“BPM 分发 + phase 交接 + 会话隔离”的运行骨架。
2. 分发策略：每个 phase 通过 `process-instance-manager` 触发真实 `openclaw` 分发。
3. 会话策略：
   - 默认开启 `--reset-openclaw-session`；
   - 同 actor 跨 phase 必须新会话，避免主会话上下文污染。
4. phase 最小语义：
   - `phase_purpose`
   - `input_context_ref`
   - `done_definition`
   - `handoff_note`
5. 当前边界：本轮以协作可运行为优先目标；各子流程真实执行在后续回合逐步接线。

<!-- phase-semantics-v2:start -->
## 阶段协作语义补充（v2）

> 说明：本节用于说明每个 phase 在系统主线中的职责与协作价值，要求可直接回答“为什么由该 Actor 在该阶段执行该动作”。

| phase_id | Actor | 阶段目的 | 输入语义 | 完成标准 | 交接语义 |
|---|---|---|---|---|---|
| `p1` | `architect` | 澄清目标并形成范围基线，为后续规格编写提供稳定输入。 | objective_context_ref,input_payload | 必须产出 objective_ref 与 scope_baseline_ref。 | 将 objective_ref 与 scope_baseline_ref 交接给 p2。 |
| `p2` | `architect` | 将目标与范围基线收敛为可执行规格。 | objective_ref,scope_baseline_ref | 必须产出 spec_ref，并可追溯到 p1 输入。 | 将 spec_ref 交接给 p3。 |
| `p3` | `qa` | 围绕规格构建测试准备包，明确后续验证基线。 | spec_ref | 必须产出 test_plan_ref 与 preparation_bundle_ref。 | 将 test_plan_ref 与 preparation_bundle_ref 交接给 p4。 |
| `p4` | `kernel-dev` | 在规格与测试基线约束下完成实现与候选产物。 | spec_ref,test_plan_ref | 必须产出 implementation_ref 与 candidate_artifacts_ref。 | 将 candidate_artifacts_ref 交接给 p5。 |
| `p5` | `qa` | 执行质量门禁评测并形成统一门禁结论。 | candidate_artifacts_ref,preparation_bundle_ref | 必须产出 final_gate_verdict_ref，且门禁结论可解释。 | 若门禁通过，则将 final_gate_verdict_ref 交接给 p6。 |
| `p6` | `admin` | 完成生命周期治理与 registry 同步前置校验。 | final_gate_verdict_ref,lifecycle_target | 必须产出 lifecycle_transition_ref 与 registry_sync_ref。 | 将 lifecycle_transition_ref 与 registry_sync_ref 交接给 p7。 |
| `p7` | `admin` | 完成发布打包与回滚包准备。 | candidate_artifacts_ref,final_gate_verdict_ref,lifecycle_transition_ref,registry_sync_ref | 必须产出 release_package_ref 与 rollback_bundle_ref。 | 将发布产物与反馈证据交接给 p8。 |
| `p8` | `architect` | 基于发布与运行反馈形成下一轮演化计划。 | release_package_ref,final_gate_verdict_ref,lifecycle_transition_ref,runtime_feedback_ref | 必须产出 improvement_plan_ref 与 retro_report_ref。 | 将演化计划回填给发起方作为下一轮输入。 |
<!-- phase-semantics-v2:end -->
