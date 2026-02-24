# hotfix-scope-spec-baseline - 流程说明

## 流程定位

- 流程级别：`P5`
- 负责人：`bpm`
- 版本：`0.1.0`
- Objective 引用：`obj-m3-hotfix-scope-spec-baseline`

## 流程目标（自然语言）

该流程用于 hotfix 场景下快速形成 scope/spec 双基线，明确爆炸半径、回滚边界与执行约束。它连接应急目标与实现执行，避免 hotfix 直接跳过规格设计。

## 协作编排原则

1. 该流程用于 hotfix 的双基线收敛，先锁定影响边界再输出可执行规格。
2. 范围基线必须显式约束爆炸半径与回滚边界，防止修复范围失控。
3. 规格输出应直接服务下游测试与实现，避免应急场景重复解释。
4. 该流程强调“快且准”的设计收口，不以文档篇幅作为完成标准。

## 阶段语义定义

### p1 hotfix-scope-baseline

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：产出包含爆炸半径控制的 hotfix 范围基线。
- 输入语义：本阶段主要消费以下输入：hotfix_objective_ref + impact_scope_ref。
- 完成标准：完成判据：必须产出 hotfix_scope_baseline_ref，并满足“范围基线包含回滚边界”。
- 交接说明：交接要求：将 hotfix_scope_baseline_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:hotfix-scope-spec-baseline:p1`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p2 hotfix-spec-authoring

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：组合规格编写契约并将 spec_ref 映射为 hotfix_spec_ref。
- 输入语义：本阶段主要消费以下输入：hotfix_scope_baseline_ref。
- 完成标准：完成判据：必须产出 hotfix_spec_ref，并满足“hotfix 规格保持 AP-004 契约且无重复定义”。
- 交接说明：交接要求：将 hotfix_spec_ref 交接给 initiator。
- 执行单元：`subprocess:spec-authoring-contract`。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
