# release-packaging-governed - 流程说明

## 流程定位

- 流程级别：`P5`
- 负责人：`bpm`
- 版本：`0.1.0`
- Objective 引用：`obj-m3-release-packaging-governed`

## 流程目标（自然语言）

该流程负责在门禁通过后生成发布包与回滚包，确保发布决策与恢复路径同时可用。它在架构中承担从“变更候选”到“可运营发布物”的最后一跳。

## 协作编排原则

1. 该流程用于将通过门禁的候选产物收敛为可运营发布包。
2. 发布包与回滚包必须成对生成，保证线上异常时可快速恢复。
3. 流程只承接已通过门禁与生命周期校验的输入，禁止前置条件缺失时打包。
4. 发布决策需可追溯到门禁证据，避免“可发布”结论无来源。

## 阶段语义定义

### p1 release-packaging

- 执行角色：`admin`
- 阶段目的：本阶段围绕以下业务动作推进：打包发布产物并形成发布决策。
- 输入语义：本阶段主要消费以下输入：candidate_artifacts 与 governed_release_prerequisites。
- 完成标准：完成判据：必须产出 release_package_ref + rollback_bundle_ref，并满足“发布决策与回滚包均明确”。
- 交接说明：交接要求：将 release_package_ref + rollback_bundle_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:release-packaging-governed:p1`。该阶段采用临时 AP 语法，映射 skill 为 `sys.admin.release-manager`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
