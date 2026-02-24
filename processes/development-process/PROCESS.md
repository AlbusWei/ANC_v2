# development-process - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.1.0`
- Objective 引用：`obj-phase0.5-development-process`

## 流程目标（自然语言）

该流程是 legacy 兼容入口，用于承接旧路径下的技能资产开发请求，并保证“需求澄清 -> 资产产出 -> 测试验证 -> registry 同步”的最小闭环。其存在意义是平滑迁移到 canonical 路径 `processes/meta/development-process/`，而不是长期并行扩张。

## 协作编排原则

1. 该流程定位为 legacy 兼容入口，目标是把旧路径请求平稳导向 canonical 研发闭环。
2. 必须完成“需求澄清 -> 资产产出 -> 测试验证 -> registry 同步”的最小治理链。
3. 流程内不引入与兼容目标无关的新治理职责，避免 legacy 路径继续膨胀。
4. 新增或修改资产必须可在 registry 中被检索与追溯，保证迁移期可审计。

## 阶段语义定义

### p1 clarify-objective-and-scope

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：澄清目标、约束与目标技能范围。
- 输入语义：本阶段主要消费以下输入：input_payload。
- 完成标准：完成判据：必须产出 normalized_requirement，并满足“目标、约束与目标技能明确”。
- 交接说明：交接要求：将 normalized_requirement 交接给 p2。
- 执行单元：`subprocess:`。

### p2 author-skill-asset

- 执行角色：`architect`
- 阶段目的：本阶段围绕以下业务动作推进：编写或更新技能资产文件。
- 输入语义：本阶段主要消费以下输入：normalized_requirement。
- 完成标准：完成判据：必须产出 skill_asset，并满足“技能资产已存在且 frontmatter 可解析”。
- 交接说明：交接要求：将 skill_asset 交接给 p3。
- 执行单元：`subprocess:`。

### p3 design-and-run-tests

- 执行角色：`qa`
- 阶段目的：本阶段围绕以下业务动作推进：设计 TEST.md 并校验契约一致性。
- 输入语义：本阶段主要消费以下输入：skill_asset。
- 完成标准：完成判据：必须产出 test_evidence，并满足“测试计划存在且证据可追溯”。
- 交接说明：交接要求：将 test_evidence 交接给 p4。
- 执行单元：`subprocess:`。

### p4 sync-registry

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：为新增或更新资产同步 registry 记录。
- 输入语义：本阶段主要消费以下输入：test_evidence。
- 完成标准：完成判据：必须产出 registry_patch_and_verdict，并满足“registry 字段与资产 frontmatter 及路径一致”。
- 交接说明：交接要求：将 registry_patch_and_verdict 交接给 initiator。
- 执行单元：`subprocess:`。

## 控制流与回退

- 未声明控制流，默认按阶段顺序执行。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试策略由上级流程或运行配置决定。
