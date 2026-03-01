# quality-gate-preparation - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.1.0`
- Objective 引用：`obj-m1-unified-quality-gate`

## 流程目标（自然语言）

该流程负责把测试设计转化为可执行准备包（plan/datapoints/profile 绑定），为后续 gate 评测提供统一输入。它在全局架构中的意义是把“测试意图”转成“可运行证据生产线”。

## 协作编排原则

1. 该流程目标是把测试意图转成可执行准备包，而不是停留在文档层面。
2. 测试设计必须显式覆盖高风险路径，确保门禁评测有判别力。
3. 编译与 profile 绑定需保持一一映射，防止执行阶段语义漂移。
4. 输出准备包必须可被评测流程直接消费，减少跨阶段二次解释。

## 阶段语义定义

### p1 design-tests

- 执行角色：`qa`
- 阶段目的：设计与目标对齐且覆盖 P0 风险的测试。
- 输入语义：objective_ref + spec_ref + test_doc_ref。
- 完成标准：必须产出 test_plan_ref，并满足“P0 风险覆盖显式且可追溯”。
- 交接说明：将 test_plan_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:quality-gate-preparation:p1`。该阶段采用临时 AP 语法，映射 skill 为 `meta.qa.test-designer`，穿透执行策略：允许（同 Actor 场景）。

### p2 compile-test-datapoints

- 执行角色：`qa`
- 阶段目的：将 TEST.md 编译为可执行数据点。
- 输入语义：test_plan_ref + test_doc_ref。
- 完成标准：必须产出 test_datapoints_ref + compile_report_ref，并满足“编译报告完整且数据点可执行”。
- 交接说明：将 test_datapoints_ref + compile_report_ref 交接给 p3。
- 执行单元：`subprocess:inline-ap:quality-gate-preparation:p2`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.test-compiler`，穿透执行策略：允许（同 Actor 场景）。

### p3 bind-test-profiles

- 执行角色：`qa`
- 阶段目的：绑定 tc_id 与 profile_id 并打包准备集。
- 输入语义：test_datapoints_ref + compile_report_ref + profile_set。
- 完成标准：必须产出 preparation_bundle_ref，并满足“tc_id 与 profile_id 映射一一对应且可追溯”。
- 交接说明：将 preparation_bundle_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:quality-gate-preparation:p3`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.test-compiler`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`。
- `p3` 在 `success` 条件下流转到 `end`。

## 协作策略（运行态）

1. 协作模式：`phase-isolated-session`。
2. 分发运行时：`openclaw-required`。
3. 会话重置策略：`per-phase-reset`。
4. phase 交接以自然语言任务说明 + 引用交接为主，不依赖隐式会话记忆。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
