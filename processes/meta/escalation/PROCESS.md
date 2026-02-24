# escalation - 流程说明

## 流程定位

- 流程级别：`P5`
- 负责人：`bpm`
- 版本：`0.1.0`
- Objective 引用：`obj-m3-escalation-runtime`

## 流程目标（自然语言）

该流程用于统一升级链路执行，确保 incident 从分级、策略校验到链路分发与收口决策都有明确责任人和证据。其意义是把“谁来处理、何时升阶”从临时判断转为制度化协作机制。

## 协作编排原则

1. 该流程目标是把升级行为制度化，避免依赖临场经验决定升级路径。
2. 升级前必须完成事件与策略归一，防止“信息不全”导致错误路由。
3. 链路分发必须遵循治理层级，不允许越级或跳链短路。
4. 收口结论必须明确为 resolved/escalated/human-required 之一，避免模糊状态。
5. 升级全过程必须可审计，确保责任与决策可回溯。

## 阶段语义定义

### p1 incident-intake

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：归一化故障事件上下文。
- 输入语义：本阶段主要消费以下输入：incident 与 severity。
- 完成标准：完成判据：必须产出 incident_snapshot_ref，并满足“事件字段与证据引用完整”。
- 交接说明：交接要求：将 incident_snapshot_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:escalation:p1`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p2 policy-check

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：校验策略与治理边界。
- 输入语义：本阶段主要消费以下输入：incident_snapshot 与 escalation_policy。
- 完成标准：完成判据：必须产出 policy_check_ref，并满足“策略可解析且链路有效”。
- 交接说明：交接要求：将 policy_check_ref 交接给 p3。
- 执行单元：`subprocess:inline-ap:escalation:p2`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p3 chain-routing

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：按治理升级链路进行分发。
- 输入语义：本阶段主要消费以下输入：policy_check_ref。
- 完成标准：完成判据：必须产出 escalation_trace，并满足“升级轨迹可审计且最终负责人在链路内”。
- 交接说明：交接要求：将 escalation_trace 交接给 p4。
- 执行单元：`subprocess:inline-ap:escalation:p3`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.escalation-handler`，穿透执行策略：允许（同 Actor 场景）。

### p4 resolution-or-human

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：以 resolved/escalated/human-required 结论收口升级。
- 输入语义：本阶段主要消费以下输入：escalation_trace。
- 完成标准：完成判据：必须产出 escalation_output_ref，并满足“决策结论明确且原因完整”。
- 交接说明：交接要求：将 escalation_output_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:escalation:p4`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.escalation-handler`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
