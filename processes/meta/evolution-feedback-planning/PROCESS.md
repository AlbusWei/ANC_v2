# evolution-feedback-planning - 流程说明

## 流程定位

- 流程级别：`P5`
- 负责人：`bpm`
- 版本：`0.2.0`
- Objective 引用：`obj-m3-evolution-feedback-planning`

## 流程目标（自然语言）

该流程负责将运行反馈与回顾结论转化为下一轮改进计划，形成 Release 之后的演化闭环。它在系统中的定位是把经验沉淀为可执行输入，驱动 ANC 的自进化而非一次性交付。

## 协作编排原则

1. 该流程是演化闭环入口，核心是把运行反馈转化为下一轮可执行计划。
2. 反馈先归一再分级，避免将噪声直接写入改进清单。
3. 改进计划必须包含优先级与负责人，防止“知道问题但无人执行”。
4. 复盘报告需与改进行动成对产出，确保经验沉淀可落地。

## 阶段语义定义

### p1 feedback-intake

- 执行角色：`system-analyst`
- 阶段目的：归一化运行反馈并提炼关键信号。
- 输入语义：feedback_evidence_ref。
- 完成标准：必须产出 feedback_digest_ref，并满足“反馈摘要完整且可追溯”。
- 交接说明：将 feedback_digest_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:evolution-feedback-planning:p1`。该阶段采用临时 AP 语法，映射 skill 为 `sys.arch.system-feedback-digest`，穿透执行策略：允许（同 Actor 场景）。

### p2 classify-and-prioritize

- 执行角色：`architect`
- 阶段目的：对问题进行分类并划定优先级分桶。
- 输入语义：feedback_digest_ref。
- 完成标准：必须产出 priority_matrix_ref，并满足“优先级矩阵包含依据与影响评估”。
- 交接说明：将 priority_matrix_ref 交接给 p3。
- 执行单元：`subprocess:inline-ap:evolution-feedback-planning:p2`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p3 draft-improvement-plan

- 执行角色：`architect`
- 阶段目的：起草下一轮改进计划。
- 输入语义：priority_matrix_ref。
- 完成标准：必须产出 improvement_plan_ref，并满足“计划包含负责人、优先级顺序与回滚方向”。
- 交接说明：将 improvement_plan_ref 交接给 p4。
- 执行单元：`subprocess:inline-ap:evolution-feedback-planning:p3`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p4 retro-and-loop-close

- 执行角色：`architect`
- 阶段目的：产出复盘报告并闭环本轮改进。
- 输入语义：improvement_plan_ref。
- 完成标准：必须产出 retro_report_ref，并满足“复盘报告与改进计划均已发布”。
- 交接说明：将 retro_report_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:evolution-feedback-planning:p4`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `end`。

## 协作策略（运行态）

1. 协作模式：`phase-isolated-session`。
2. 分发运行时：`openclaw-required`。
3. 会话重置策略：`per-phase-reset`。
4. 跨角色交接优先使用自然语言任务说明 + 引用交接，不依赖隐式会话记忆。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
