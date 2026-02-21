# HOLD Governance Process

> 版本: v0.2.0 | 层级: P4 | 类型: 复合流程 | process_id: hold-governance

## 目标

将 `hold` 状态治理沉淀为标准化复合流程，统一处理进展证据、triage 决策、动作执行、运行健康维护与关闭升级。

## 触发条件

1. `quality-gate-evaluation` 任一分项评测进入 `hold`
2. 运行任务具备长时执行特征且需活性确认
3. `M2` 检测到流程卡滞但未满足直接 `fail` 条件

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

1. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/atomic/AP-021-hold-progress-evidence-collection.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/atomic/AP-022-hold-triage-classification.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/atomic/AP-023-hold-triage-action-execution.md`
4. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/atomic/AP-024-runtime-health-maintenance.md`
5. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/atomic/AP-025-hold-resolution-and-escalation.md`
