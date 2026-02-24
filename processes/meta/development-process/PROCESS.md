# development-process - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.3.0`
- Objective 引用：`obj-phase1-min-loop`

## 流程目标（自然语言）

该流程是内部开发闭环的轻量主干，聚焦 Objective -> Spec -> Test -> Implementation -> Gate 五段，确保每次实现都由目标牵引并受测试门禁约束。它在全局架构中的作用是为上层业务流程提供稳定的“可验证实现”子流程能力。

## 协作编排原则

1. 该流程只承担“可验证实现”最小闭环，不扩展发布与演化职责。
2. 目标与范围基线必须先于规格与实现产出，防止需求漂移放大返工。
3. 测试准备与门禁评测是强制链路，不能以“实现已完成”替代质量结论。
4. 失败回路仅在 `p5 -> p4` 闭环内修订，避免跨阶段无界回退。
5. 输出应作为上级业务流程可复用能力，而非单次任务脚本。

## 阶段语义定义

### p1 objective-scope-baseline

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：归一化目标与范围基线。
- 输入语义：本阶段主要消费以下输入：objective_context_ref。
- 完成标准：完成判据：必须产出 objective_ref + scope_baseline_ref，并满足“目标与范围基线完整”。
- 交接说明：交接要求：将 objective_ref + scope_baseline_ref 交接给 p2。
- 执行单元：`subprocess:objective-scope-baseline`。

### p2 spec-authoring-contract

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：产出可执行规格。
- 输入语义：本阶段主要消费以下输入：objective_ref + scope_baseline_ref。
- 完成标准：完成判据：必须产出 spec_ref，并满足“规格契约可解析且可审计”。
- 交接说明：交接要求：将 spec_ref 交接给 p3。
- 执行单元：`subprocess:spec-authoring-contract`。

### p3 quality-gate-preparation

- 执行角色：`qa`
- 阶段目的：本阶段围绕以下业务动作推进：准备质量门禁测试计划。
- 输入语义：本阶段主要消费以下输入：spec_ref。
- 完成标准：完成判据：必须产出 test_plan_ref，并满足“测试计划完整且可追溯”。
- 交接说明：交接要求：将 test_plan_ref 交接给 p4。
- 执行单元：`subprocess:quality-gate-preparation`。

### p4 implementation-execution-core

- 执行角色：`kernel-dev`
- 阶段目的：本阶段围绕以下业务动作推进：产出实现候选物。
- 输入语义：本阶段主要消费以下输入：spec_ref + test_plan_ref。
- 完成标准：完成判据：必须产出 implementation_ref，并满足“实现产物已生成并与测试建立关联”。
- 交接说明：交接要求：将 implementation_ref 交接给 p5。
- 执行单元：`subprocess:implementation-execution-core`。

### p5 quality-gate-evaluation

- 执行角色：`qa`
- 阶段目的：本阶段围绕以下业务动作推进：按目标与测试条件评估候选产物。
- 输入语义：本阶段主要消费以下输入：implementation_ref。
- 完成标准：完成判据：必须产出 final_gate_verdict_ref，并满足“结论包含 pass/fail 与证据引用”。
- 交接说明：交接要求：将 final_gate_verdict_ref 交接给 initiator。
- 执行单元：`subprocess:quality-gate-evaluation`。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `p5`。
- `p5` 在 `failure` 条件下流转到 `p4`（条件：iterations < 2）。
- `p5` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_iterations=2, from_phase=p5, to_phase=p4。
