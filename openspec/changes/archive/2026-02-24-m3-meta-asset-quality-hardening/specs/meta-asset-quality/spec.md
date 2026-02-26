## ADDED Requirements

### Requirement: Meta Asset Quality Gate V1 Must Be Enforced For All Meta Skills And Meta Processes
Meta 资产质量门禁 MUST 覆盖全部 Meta 技能与 Meta 流程，并作为生命周期推进前置。

#### Scenario: Quality gate rejects incomplete capability/process contracts
- **WHEN** 任一 Meta 技能或 Meta 流程缺少执行步骤、Fail-Closed 规则、运行入口或测试挂载
- **THEN** 质量门禁返回 fail
- **AND** 该资产不得推进到 `review`

### Requirement: Core Meta Creator Contracts Must Be Upgraded To Execution-Grade Field-Level Contracts
`meta.arch.agent-creator`、`meta.arch.process-creator`、`meta.arch.template-validator`、`meta.arch.skill-creator` MUST 升级为字段级可执行契约。

#### Scenario: Creator contract outputs registry/linkage/validation artifacts
- **WHEN** Creator 类技能接收完整输入
- **THEN** 输出必须包含 registry patch plan、linkage patch plan、validation report 引用
- **AND** 若关键字段缺失必须 Fail-Closed 并给出结构化阻断原因

### Requirement: Lifecycle Promotion In This Change Must Be Capped At Review
本 change 中整改资产生命周期 MUST 收敛到 `review` 且 MUST NOT 推进 `active`。

#### Scenario: Any active promotion attempt is blocked
- **WHEN** 执行状态迁移时请求 `review -> active`
- **THEN** 门禁必须阻断并返回 fail-closed 决策
- **AND** 记录阻断证据到本回合证据目录

### Requirement: QA Runtime-First Validation Must Be The Primary Acceptance Mechanism
主验收机制 MUST 以 QA 在线运行结果为准，静态校验仅作为基础门禁。

#### Scenario: Static pass but runtime fail still blocks phase close
- **WHEN** `registry verify` 与 `openspec validate` 通过但 openclaw 在线 case 失败
- **THEN** phase close 必须判定失败
- **AND** 必须进入缺陷修复与回归流程
