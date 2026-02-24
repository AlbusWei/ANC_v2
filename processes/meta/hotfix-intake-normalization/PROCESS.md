# hotfix-intake-normalization - 流程说明

## 流程定位

- 流程级别：`P5`
- 负责人：`bpm`
- 版本：`0.1.0`
- Objective 引用：`obj-m3-hotfix-intake-normalization`

## 流程目标（自然语言）

该流程负责将事故输入归一为可执行 hotfix 目标，明确影响面与回滚方向。它的价值是把“故障描述”转成“可交付任务定义”，为后续快速链路建立稳定起点。

## 协作编排原则

1. 该流程把事故描述转化为可执行 hotfix 任务定义，是应急链路的入口治理。
2. 必须同时明确目标、影响范围与回滚方向，三者缺一不可。
3. 输入归一后的输出要能被下游直接消费，减少应急过程中的语义偏差。
4. 任何关键信息缺失都应阻断推进并触发补充，而非猜测性继续。

## 阶段语义定义

### p1 hotfix-objective-intake

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：从故障上下文中提炼 hotfix 目标。
- 输入语义：本阶段主要消费以下输入：incident_context_ref。
- 完成标准：完成判据：必须产出 hotfix_objective_ref，并满足“hotfix 目标明确且边界清晰”。
- 交接说明：交接要求：将 hotfix_objective_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:hotfix-intake-normalization:p1`。该阶段采用临时 AP 语法，映射 skill 为 `meta.arch.objective-writer`，穿透执行策略：允许（同 Actor 场景）。

### p2 impact-and-rollback-normalization

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：归一化影响范围与回滚方向。
- 输入语义：本阶段主要消费以下输入：hotfix_objective_ref。
- 完成标准：完成判据：必须产出 impact_scope_ref + rollback_direction_ref，并满足“影响范围与回滚方向可直接执行”。
- 交接说明：交接要求：将 impact_scope_ref + rollback_direction_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:hotfix-intake-normalization:p2`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
