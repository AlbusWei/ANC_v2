# implementation-execution-core - 流程说明

## 流程定位

- 流程级别：`P5`
- 负责人：`bpm`
- 版本：`0.1.0`
- Objective 引用：`obj-m3-implementation-execution-core`

## 流程目标（自然语言）

该流程是开发实施的原子执行核心，目标是在既定 spec 与 test 约束下产出可评测候选产物。它把“编码动作”纳入流程证据链，保证实现结果可回放、可验证。

## 协作编排原则

1. 该流程只承担实现执行，不负责替代目标定义或质量裁决。
2. 实现输入必须绑定 spec 与 test 基线，避免“凭感觉编码”。
3. 输出候选产物需保持对规格与测试的可追溯性，支持后续门禁评测。
4. 遇到约束冲突时应回退上游修订，而不是在实现阶段私自改需求。

## 阶段语义定义

### p1 implementation-execution

- 执行角色：`kernel-dev`
- 阶段目的：按规格与测试执行候选实现。
- 输入语义：spec_ref + test_plan_ref。
- 完成标准：必须产出 implementation_ref，并满足“实现保持对规格与测试的可追溯性”。
- 交接说明：将 implementation_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:implementation-execution-core:p1`。该阶段采用临时 AP 语法，映射 skill 为 `system.ops.manual-task`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
