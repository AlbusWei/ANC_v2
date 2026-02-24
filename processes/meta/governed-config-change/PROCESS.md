# governed-config-change - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.2.0`
- Objective 引用：`obj-governed-openclaw-config-change`

## 流程目标（自然语言）

该流程用于高风险 OpenClaw 配置变更的治理执行，将请求归一、风险门禁、授权、执行与事后核验串成强审计链。其架构意义是把系统级写操作从“人肉命令”提升为“可回执、可回滚、可追责”的流程行为。

## 协作编排原则

1. 该流程用于高风险配置写操作治理，任何执行都必须经过门禁与授权。
2. `admin` 授权结论是执行前置条件，`bpm` 不得越权直接落地系统改动。
3. 配置变更必须以 `baseHash` 为一致性锚点，并保留前后状态回执。
4. 执行后必须完成健康核验与证据归档，保证“改了什么、影响如何”可追踪。
5. 失败场景优先进入可恢复治理路径，不以手工补命令掩盖流程断点。

## 阶段语义定义

### p1 intake-and-normalize

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：将请求归一为结构化 config_change_request。
- 输入语义：本阶段主要消费以下输入：change_request。
- 完成标准：完成判据：必须产出 normalized_request，并满足“请求包含目标范围、预期影响与回滚方案”。
- 交接说明：交接要求：将 normalized_request 交接给 p2。
- 执行单元：`subprocess:inline-ap:governed-config-change:p1`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p2 gate-and-risk-classification

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：校验必需证据并完成风险分级。
- 输入语义：本阶段主要消费以下输入：normalized_request。
- 完成标准：完成判据：必须产出 approved_request，并满足“objective/spec/test 链路完整且风险等级已记录”。
- 交接说明：交接要求：将 approved_request 交接给 p3。
- 执行单元：`subprocess:inline-ap:governed-config-change:p2`。该阶段采用临时 AP 语法，映射 skill 为 `system.control.config-change-gatekeeper`，穿透执行策略：允许（同 Actor 场景）。

### p3 authorize-change

- 执行角色：`admin`
- 阶段目的：本阶段围绕以下业务动作推进：批准或驳回执行窗口与变更范围。
- 输入语义：本阶段主要消费以下输入：approved_request。
- 完成标准：完成判据：必须产出 authorization_decision，并满足“授权决策包含批准结果、约束条件与回滚触发条件”。
- 交接说明：交接要求：将 authorization_decision 交接给 p4。
- 执行单元：`subprocess:inline-ap:governed-config-change:p3`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p4 execute-config-change

- 执行角色：`admin`
- 阶段目的：本阶段围绕以下业务动作推进：基于 baseHash 执行 OpenClaw 配置变更并记录回执。
- 输入语义：本阶段主要消费以下输入：authorization_decision。
- 完成标准：完成判据：必须产出 change_receipt，并满足“变更回执包含 hash_before/hash_after、补丁摘要与执行状态”。
- 交接说明：交接要求：将 change_receipt 交接给 p5。
- 执行单元：`subprocess:inline-ap:governed-config-change:p4`。该阶段采用临时 AP 语法，映射 skill 为 `system.admin.system-config-updater`，穿透执行策略：允许（同 Actor 场景）。

### p5 verify-and-archive

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：校验变更后健康状态、归档证据并通知请求方。
- 输入语义：本阶段主要消费以下输入：change_receipt。
- 完成标准：完成判据：必须产出 final_output，并满足“健康校验通过且证据包完整”。
- 交接说明：交接要求：将 final_output 交接给 initiator。
- 执行单元：`subprocess:inline-ap:governed-config-change:p5`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `p5`。
- `p5` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
