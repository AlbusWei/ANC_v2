# hold-governance - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.3.0`
- Objective 引用：`obj-m1-unified-quality-gate`

## 流程目标（自然语言）

该流程用于处理 quality gate 产出的 hold 案例，目标是把“卡住”变成可诊断、可处置、可升级的治理路径。它在系统中承担异常恢复中枢，防止流程长期悬挂或无责任归属，并确保对外门禁保持 Fail-Closed。

## 协作编排原则

1. 该流程只处理 hold 异常治理，不承担普通通过路径的快速放行职责。
2. 先收集进展信号再分级决策，禁止先下结论后补证据。
3. 处置动作必须与分诊结论一致，避免“判了 A 执行 B”的语义漂移。
4. 健康维护与恢复评估是收口前置条件，确保解除 hold 后可持续运行。
5. 无法闭环时必须升级并保留完整轨迹，防止 hold 长期悬置。

## 阶段语义定义

### p1 collect-progress-evidence

- 执行角色：`qa`
- 阶段目的：收集最小进展信号集。
- 输入语义：hold_case_ref + runtime_log_ref + execution_state_ref + liveness_policy_ref + no_progress_window_ref。
- 完成标准：必须产出 progress_signals_ref，并满足“三类进展信号已收集或已明确记录失败原因”。
- 交接说明：将 progress_signals_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:hold-governance:p1`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.hold-triage`，穿透执行策略：允许（同 Actor 场景）。

### p2 triage-and-classify

- 执行角色：`qa`
- 阶段目的：对 hold 场景进行处置分级。
- 输入语义：progress_signals_ref + triage_policy_ref。
- 完成标准：必须产出 triage_action，并满足“分诊动作明确且符合策略”。
- 交接说明：将 triage_action 交接给 p3。
- 执行单元：`subprocess:inline-ap:hold-governance:p2`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.hold-triage`，穿透执行策略：允许（同 Actor 场景）。

### p3 execute-triage-action

- 执行角色：`qa`
- 阶段目的：执行选定的分诊动作。
- 输入语义：triage_action + triage_report_ref。
- 完成标准：必须产出 action_execution_ref，并满足“动作执行与分诊决策一致”。
- 交接说明：将 action_execution_ref 交接给 p4。
- 执行单元：`subprocess:inline-ap:hold-governance:p3`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.hold-triage`，穿透执行策略：允许（同 Actor 场景）。

### p4 health-maintenance

- 执行角色：`bpm`
- 阶段目的：维护运行时健康与恢复状态。
- 输入语义：action_execution_ref + runtime_health_policy_ref + no_progress_window_ref + termination_rule_ref。
- 完成标准：必须产出 health_maintenance_ref，并满足“健康结果可追溯且可恢复性明确”。
- 交接说明：将 health_maintenance_ref 交接给 p5。
- 执行单元：`subprocess:inline-ap:hold-governance:p4`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.process-instance-manager`，穿透执行策略：允许（同 Actor 场景）。

### p5 close-or-escalate

- 执行角色：`bpm`
- 阶段目的：收敛 hold 案例并给出回测建议。
- 输入语义：triage_action + health_maintenance_ref + termination_rule_ref。
- 完成标准：必须产出 hold_resolution_ref + retest_recommendation + external_gate_decision，并满足“hold 案例按治理链路收敛或升级且对外门禁保持 fail-closed”。
- 交接说明：将 hold_resolution_ref + retest_recommendation + external_gate_decision 交接给 initiator。
- 执行单元：`subprocess:inline-ap:hold-governance:p5`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.escalation-handler`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `p5`。
- `p5` 在 `success` 条件下流转到 `end`。

## 协作策略（运行态）

1. 协作模式：`phase-isolated-session`。
2. 分发运行时：`openclaw-required`。
3. 会话重置策略：`per-phase-reset`。
4. phase 交接以自然语言任务说明 + 引用交接为主，不依赖隐式会话记忆。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
5. 无进展窗口阈值缺失或小于 900 秒时，禁止终止并 Fail-Closed。
