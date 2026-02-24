# objective-scope-baseline - 流程说明

## 流程定位

- 流程级别：`P5`
- 负责人：`bpm`
- 版本：`0.1.0`
- Objective 引用：`obj-m3-objective-scope-baseline`

## 流程目标（自然语言）

该流程用于在开发前固化 Objective 与 Scope 基线，明确边界、非目标与成功判据。它的架构作用是为后续 Spec/Test/Development 提供稳定起点，减少需求漂移导致的返工。

## 协作编排原则

1. 该流程只负责定义“做什么/不做什么”，不提前进入实现细节。
2. 目标表达必须可衡量、可验证，不能停留在抽象愿景。
3. 范围基线需显式包含边界与非目标，作为后续规格约束锚点。
4. 完成态应支持下游直接编写 spec，而无需再次解释目标语义。

## 阶段语义定义

### p1 objective-intake

- 执行角色：`architect`
- 阶段目的：提炼目标与成功判据基线。
- 输入语义：objective_context_ref。
- 完成标准：必须产出 objective_ref，并满足“目标具备可衡量范围且约束明确”。
- 交接说明：将 objective_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:objective-scope-baseline:p1`。该阶段采用临时 AP 语法，映射 skill 为 `meta.arch.objective-writer`，穿透执行策略：允许（同 Actor 场景）。

### p2 scope-normalization

- 执行角色：`architect`
- 阶段目的：归一化范围边界与非目标。
- 输入语义：objective_ref。
- 完成标准：必须产出 scope_draft_ref，并满足“范围草案包含边界与排除域”。
- 交接说明：将 scope_draft_ref 交接给 p3。
- 执行单元：`subprocess:inline-ap:objective-scope-baseline:p2`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

### p3 scope-baseline-finalization

- 执行角色：`architect`
- 阶段目的：固化治理化范围基线。
- 输入语义：scope_draft_ref。
- 完成标准：必须产出 scope_baseline_ref，并满足“范围基线可追溯且无冲突”。
- 交接说明：将 scope_baseline_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:objective-scope-baseline:p3`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
