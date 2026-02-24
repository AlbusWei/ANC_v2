# HOLD Governance Process

> 版本: v0.2.0 | 层级: P4 | 类型: 复合流程 | process_id: hold-governance

## 目标

将 `hold` 状态治理沉淀为标准化复合流程，统一处理进展证据、triage 决策、动作执行、运行健康维护与关闭升级。

## 触发条件

1. `quality-gate-evaluation` 任一分项评测进入 `hold`
2. 运行任务具备长时执行特征且需活性确认
3. `M2` 检测到流程卡滞但未满足直接 `fail` 条件

## 生命周期与调度状态

1. Registry 生命周期：`review`（W3-B）。
2. Runtime 入口：`processes/meta/hold-governance/scripts/hold_governance_runner.py`。
3. 当前由 `quality-gate-evaluation` 的 `p5 govern-hold` 子流程调用。

## 阶段定义

1. `collect-progress-evidence`（AP-021）
2. `triage-and-classify`（AP-022）
3. `execute-triage-action`（AP-023）
4. `health-maintenance`（AP-024）
5. `close-or-escalate`（AP-025）

## 阶段到原子流程映射

| 阶段 | 原子流程 | Actor | Skill | 输出 |
|---|---|---|---|---|
| collect-progress-evidence | AP-021 | qa / qa-engineer | sys.qa.hold-triage | progress_signals_ref |
| triage-and-classify | AP-022 | qa / qa-engineer | sys.qa.hold-triage | triage_action + triage_report_ref |
| execute-triage-action | AP-023 | qa / qa-engineer | sys.qa.hold-triage | action_execution_ref |
| health-maintenance | AP-024 | bpm | sys.bpm.process-instance-manager | health_maintenance_ref |
| close-or-escalate | AP-025 | bpm | sys.bpm.escalation-handler | hold_resolution_ref |

## 输入契约

1. `hold_case_ref`
2. `runtime_log_ref`
3. `execution_state_ref`
4. `triage_policy_ref`
5. `runtime_health_policy_ref`

## 输出契约

1. `triage_report_ref`
2. `health_maintenance_ref`
3. `hold_resolution_ref`
4. `escalation_ref`（可选）

## 决策枚举

1. `continue`
2. `retry`
3. `debug`
4. `fail`

## 升级链

`qa -> bpm -> admin`

## Fail-Closed 规则

1. 进展信号缺失且无法补证 -> `fail`
2. triage 无明确决策 -> `fail`
3. 证据链缺失或不可追溯 -> `fail`
4. 禁止以固定超时阈值直接判定失败

## 依赖流程

1. `docs/design/processes/atomic/AP-021-hold-progress-evidence-collection.md`
2. `docs/design/processes/atomic/AP-022-hold-triage-classification.md`
3. `docs/design/processes/atomic/AP-023-hold-triage-action-execution.md`
4. `docs/design/processes/atomic/AP-024-runtime-health-maintenance.md`
5. `docs/design/processes/atomic/AP-025-hold-resolution-and-escalation.md`

## W3-B 运行级证据

1. HOLD 路由 case：`docs/design/modules/evidence/bpm-runtime/w3b_qa_process_cases/TC-QA-PROC-002/`
2. 子流程输出：`docs/design/modules/evidence/bpm-runtime/w3b_qa_process_cases/TC-QA-PROC-002/evaluation/p5_hold_governance_output.json`
3. 治理闭环输出：`docs/design/modules/evidence/bpm-runtime/w3b_qa_process_cases/TC-QA-PROC-002/evaluation/p5_hold_governance/p5_hold_resolution.json`

<!-- phase-semantics-v2:start -->
## 阶段协作语义补充（v2）

> 说明：本节用于说明每个 phase 在系统主线中的职责与协作价值，要求可直接回答“为什么由该 Actor 在该阶段执行该动作”。

| phase_id | Actor | 阶段目的 | 输入语义 | 完成标准 | 交接语义 |
|---|---|---|---|---|---|
| `p1` | `qa` | 收集最小进展信号集。 | hold_case_ref + runtime_log_ref + execution_state_ref | 产出 progress_signals_ref，并满足：三类进展信号已收集或已明确记录失败原因 | 将 progress_signals_ref 交接给 p2 |
| `p2` | `qa` | 对 hold 场景进行处置分级。 | progress_signals_ref + triage_policy_ref | 产出 triage_action，并满足：分诊动作明确且符合策略 | 将 triage_action 交接给 p3 |
| `p3` | `qa` | 执行选定的分诊动作。 | triage_action + triage_report_ref | 产出 action_execution_ref，并满足：动作执行与分诊决策一致 | 将 action_execution_ref 交接给 p4 |
| `p4` | `bpm` | 维护运行时健康与恢复状态。 | action_execution_ref + runtime_health_policy_ref | 产出 health_maintenance_ref，并满足：健康结果可追溯且可恢复性明确 | 将 health_maintenance_ref 交接给 p5 |
| `p5` | `bpm` | 收敛 hold 案例或继续升级。 | triage_action + health_maintenance_ref | 产出 hold_resolution_ref，并满足：hold 案例按治理链路收敛或升级 | 将 hold_resolution_ref 交接给 initiator |
<!-- phase-semantics-v2:end -->
