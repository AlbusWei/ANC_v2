# development-process - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.4.0`
- Objective 引用：`obj-phase1-min-loop`
- 流程角色：业务开发流程的“最小开发内核”

## 流程目标（自然语言）

`development-process` 的存在意义不是替代 `full-development/hotfix/refactor`，而是提供一条最小但可执行的开发主干：
先把目标与范围澄清，再形成规格与测试准备，随后实现并给出门禁结论。它在架构中的位置是“下游流程可复用的标准开发段”，让不同业务场景在不引入发布与生命周期治理成本的情况下，先跑通可验证实现闭环。

## 协作编排原则

1. 本流程只负责“开发内核”五段，不承载 release、lifecycle、evolution 等扩展治理职责。
2. 多角色协作以阶段交接为中心：architect 负责目标与规格语义，qa 负责验证基线与门禁裁决，kernel-dev 负责实现候选物。
3. 每个 phase 必须给下一 phase 提供可直接消费的输入引用，避免“同会话口头传达”导致语义漂移。
4. 默认采用 phase 级 isolated session，保证同 actor 跨阶段不复用污染上下文。
5. 当门禁失败时，仅允许在 `p5 -> p4` 回路内迭代，不允许无界回退。

## 阶段语义定义

### p1 objective-scope-baseline

- 执行角色：`architect`
- 阶段目的：把开发需求收敛成可执行目标与范围基线，明确本轮“做什么/不做什么”。
- 输入语义：`objective_context_ref`
- 完成标准：必须产出 `objective_ref` + `scope_baseline_ref`，并明确非目标范围。
- 交接说明：将 `objective_ref` + `scope_baseline_ref` 交接给 `p2`。
- 执行单元：`subprocess:objective-scope-baseline`

### p2 spec-authoring-contract

- 执行角色：`architect`
- 阶段目的：将目标与范围基线翻译为可执行规格，形成开发与测试共同语义。
- 输入语义：`objective_ref` + `scope_baseline_ref`
- 完成标准：必须产出 `spec_ref`，且规格包含验收标准与必要约束。
- 交接说明：将 `spec_ref` 交接给 `p3`。
- 执行单元：`subprocess:spec-authoring-contract`

### p3 quality-gate-preparation

- 执行角色：`qa`
- 阶段目的：在实现前建立测试准备，保证后续实现可以被验证。
- 输入语义：`spec_ref`
- 完成标准：必须产出 `test_plan_ref`，并覆盖关键链路验证方法。
- 交接说明：将 `test_plan_ref` 交接给 `p4`。
- 执行单元：`subprocess:quality-gate-preparation`

### p4 implementation-execution-core

- 执行角色：`kernel-dev`
- 阶段目的：在规格与测试约束下产出实现候选物。
- 输入语义：`spec_ref` + `test_plan_ref`
- 完成标准：必须产出 `implementation_ref`，并与规格/测试建立映射。
- 交接说明：将 `implementation_ref` 交接给 `p5`。
- 执行单元：`subprocess:implementation-execution-core`

### p5 quality-gate-evaluation

- 执行角色：`qa`
- 阶段目的：输出统一门禁结论，供上层流程决定放行、回退或终止。
- 输入语义：`implementation_ref` + `test_plan_ref` + `objective_ref`
- 完成标准：必须产出 `final_gate_verdict_ref`，包含 pass/fail 与关键证据。
- 交接说明：成功回交发起方；失败按回路回流 `p4`。
- 执行单元：`subprocess:quality-gate-evaluation`

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `p5`。
- `p5` 在 `failure` 条件下流转到 `p4`（条件：`iterations < 2`）。
- `p5` 在 `success` 条件下流转到 `end`。

## 协作策略（运行态）

1. 协作模式：`phase-isolated-session`。
2. 分发运行时：`openclaw-required`。
3. 会话重置策略：`per-phase-reset`。
4. 输入输出优先使用自然语言上下文 + 引用标识，不以格式填充替代语义澄清。

## Fail-Closed 触发条件

1. 任一 phase 输入缺失或语义不可执行。
2. 任一 phase 输出不能支撑下一阶段继续推进。
3. 门禁阶段无法给出可解释结论或证据引用。
4. 回退超过允许次数（`max_iterations=2`）。
