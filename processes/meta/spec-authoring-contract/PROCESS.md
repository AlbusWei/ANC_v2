# spec-authoring-contract - 流程说明

## 流程定位

- 流程级别：`P5`
- 负责人：`bpm`
- 版本：`0.1.0`
- Objective 引用：`obj-m3-spec-authoring-contract`

## 流程目标（自然语言）

该流程用于把 Objective/Scope 转化为可执行规格契约，明确不变量、约束与验收语义。它在全局中承担设计-实现之间的桥梁角色，防止直接从目标跳到编码。

## 协作编排原则

1. 该流程负责把 Objective/Scope 转化为可执行规格契约，是设计到实现的桥梁。
2. 规格必须明确约束、边界与验收语义，避免后续实现阶段二次猜测。
3. 输出应可直接驱动测试准备与实现执行，减少跨阶段语义损耗。
4. 若输入目标或范围不稳定，应回退上游而非产出低质量 spec。

## 阶段语义定义

### p1 spec-authoring

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：产出可执行规格契约。
- 输入语义：本阶段主要消费以下输入：objective_ref + scope_baseline_ref。
- 完成标准：完成判据：必须产出 spec_ref，并满足“规格可解析并关联 objective/scope”。
- 交接说明：交接要求：将 spec_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:spec-authoring-contract:p1`。该阶段采用临时 AP 语法，映射 skill 为 `meta.arch.spec-writer`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
