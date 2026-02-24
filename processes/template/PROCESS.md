# process-template - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.2.0`
- Objective 引用：`obj-template`

## 流程目标（自然语言）

该模板用于快速创建“可执行而非仅格式化”的流程骨架。它不替代业务设计，而是确保新流程从第一版就具备：
可调度 phase、明确交接、可回退控制流和可落盘证据字段。

## 协作编排原则

1. 模板只提供结构，不提供业务结论；所有阶段语义必须由实际流程 owner 重写。
2. 默认采用 `phase-isolated-session`，避免把阶段协作退化为单会话对话。
3. `inline_ap` 仅用于临时承载 AP 语义，后续可逐步收敛为显式子流程。
4. 模板流程也必须遵守 Fail-Closed，不提供“样例豁免”。

## 阶段语义定义

### p1 clarify-objective

- 执行角色：`architect`
- 阶段目的：将输入需求收敛为可执行目标与边界。
- 输入语义：`objective_context_ref`
- 完成标准：产出 `normalized_requirement_ref`，并明确约束与非目标。
- 交接说明：将 `normalized_requirement_ref` 交接给 `p2`。
- 执行单元：`subprocess:inline-ap:process-template:p1`（`skill_id=system.ops.manual-task`）。

### p2 execute-main

- 执行角色：`kernel-dev`
- 阶段目的：执行核心任务并输出候选产物。
- 输入语义：`normalized_requirement_ref`
- 完成标准：产出 `deliverable_ref`，且产物可追溯到目标输入。
- 交接说明：将 `deliverable_ref` 交接给 `p3`。
- 执行单元：`subprocess:inline-ap:process-template:p2`（`skill_id=system.ops.manual-task`）。

### p3 verify-objective

- 执行角色：`qa`
- 阶段目的：评估产物是否达成目标并输出结论。
- 输入语义：`deliverable_ref`, `normalized_requirement_ref`
- 完成标准：产出 `final_verdict_ref`，包含结论与原因。
- 交接说明：将 `final_verdict_ref` 交接给 `initiator`；失败时按控制流回到 `p2`。
- 执行单元：`subprocess:inline-ap:process-template:p3`（`skill_id=system.ops.manual-task`）。

## 控制流与回退

- `p1 -> p2`：`success`
- `p2 -> p3`：`success`
- `p3 -> p2`：`failure`（`iterations < max_iterations`， max_iterations视上游输入决定，默认值为1）
- `p3 -> end`：`success`

## 协作策略（运行态）

1. 协作模式：`phase-isolated-session`。
2. 分发运行时：`openclaw-required`。
3. 会话重置策略：`per-phase-reset`。
4. 输入输出优先使用自然语言上下文 + 引用交接，不用模板话术替代设计意图。

## Fail-Closed 触发条件

1. 任一阶段输入不可解析或语义不完整。
2. 任一阶段输出无法支撑下一阶段。
3. 证据字段缺失导致不可追溯。
4. 超过回退上限仍无法收敛。
