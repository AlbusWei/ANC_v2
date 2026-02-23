# Full Development Process

> 版本: v0.2.0 | 层级: P4 | 类型: 复合流程 | process_id: full-development | process_type: dev.internal-productization

## 目标

用于内部系统资产（Agent/Skill/Process）的全链路开发闭环，覆盖 Objective 到 lifecycle/release 的标准路径。

## 连续性边界

1. 本流程通过“开发前准备 -> 实现断点 -> 开发后评测 -> 生命周期治理”的分段编排满足连续性约束。
2. `quality-gate-preparation` 与 `quality-gate-evaluation` 不在同一子流程中硬拼，由本上级流程跨断点编排。
3. 生命周期状态迁移与 registry 同步属于治理段，不在实现段提前执行。

## 阶段定义

1. `objective-intake-and-scope`（AP-001/002/003）
2. `spec-authoring`（AP-004）
3. `quality-gate-preparation`（子流程 `quality-gate-preparation`，内部覆盖 AP-005/018/019）
4. `implementation-execution`（AP-006）
5. `quality-gate-evaluation`（子流程 `quality-gate-evaluation`，内部覆盖 AP-007/008/009/020）
6. `lifecycle-gate-sync`（AP-010/011）
7. `release-packaging`（AP-012）
8. `evolution-feedback-planning`（AP-013/014/015/017）

## 阶段到流程映射

| 阶段 | 流程映射 | 输出 |
|---|---|---|
| objective-intake-and-scope | AP-001, AP-002, AP-003 | objective_ref + scope_baseline_ref |
| spec-authoring | AP-004 | spec_ref |
| quality-gate-preparation | 子流程 quality-gate-preparation（内部：AP-005, AP-018, AP-019） | preparation_bundle_ref |
| implementation-execution | AP-006 | implementation_ref |
| quality-gate-evaluation | 子流程 quality-gate-evaluation（内部：AP-007, AP-008, AP-009, AP-020） | gate_decision + final_gate_verdict_ref |
| lifecycle-gate-sync | AP-010, AP-011 | lifecycle_transition_ref + registry_sync_ref |
| release-packaging | AP-012 | release_package_ref |
| evolution-feedback-planning | AP-013, AP-014, AP-015, AP-017 | improvement_plan_ref + retro_report_ref |

## 治理绑定实施蓝图（Session2 设计闭合）

### process_type 固定值

1. `process_type = dev.internal-productization`

### governance_bundle 固定引用

1. `syntax_ref`: `docs/design/processes/development-loop-core-standard.md`
2. `obligation_ref`: `docs/design/processes/development-loop-core-standard.md`
3. `risk_policy_ref`: `docs/design/processes/governance-processes.md`
4. `checklist_ref`: `docs/design/modules/M3-self-development.md`

说明：

1. Session2 先闭合设计口径，Session3 再将字段写入 `processes/meta/full-development/process.json`。
2. 任一引用不可达时，流程实例启动必须 Fail-Closed。

## phase 目标态映射（用于 Session3 manifest 改造）

| phase_id | 阶段 | 目标 target_type | 目标 target_id | AP/子流程映射 |
|---|---|---|---|---|
| p1 | objective-intake-and-scope | atomic | AP-001/AP-002/AP-003 包装执行单元 | AP-001, AP-002, AP-003 |
| p2 | spec-authoring | atomic | AP-004 包装执行单元 | AP-004 |
| p3 | quality-gate-preparation | subprocess | quality-gate-preparation | AP-005, AP-018, AP-019 |
| p4 | implementation-execution | atomic | AP-006 包装执行单元 | AP-006 |
| p5 | quality-gate-evaluation | subprocess | quality-gate-evaluation | AP-007, AP-008, AP-009, AP-020 |
| p6 | lifecycle-gate-sync | subprocess | lifecycle-review | AP-010, AP-011 |
| p7 | release-packaging | atomic | AP-012 包装执行单元 | AP-012 |
| p8 | evolution-feedback-planning | atomic | AP-013/AP-014/AP-015/AP-017 包装执行单元 | AP-013, AP-014, AP-015, AP-017 |

约束：

1. phase 禁止继续直连 `target_type=skill`。
2. 原子执行单元在 Session3 落地为可调度 AP 包装流程后方可写入 manifest。

## 输入契约

1. `objective_ref`
2. `input_payload`
3. `target_asset_type`（`agent|skill|process`）
4. `lifecycle_target`
5. `release_required`

## 输出契约

1. `m3_delivery_bundle_ref`
2. `final_gate_verdict_ref`
3. `lifecycle_transition_ref`
4. `registry_sync_ref`
5. `release_package_ref`（可选）

## Fail-Closed 规则

1. Objective/Spec/Test 任一证据缺失时阻断实现。
2. `quality-gate-evaluation` 非 `pass` 时阻断 lifecycle/release。
3. lifecycle 或 registry 证据缺失时阻断交付并触发升级。
4. phase 未映射到已定义 AP 或子流程时拒绝流程启动。

## 依赖流程

1. `docs/design/processes/quality-gate-preparation-process.md`
2. `docs/design/processes/quality-gate-evaluation-process.md`
3. `docs/design/processes/hold-governance-process.md`
