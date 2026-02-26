# process-architecture-refactor Specification

## Purpose
定义流程架构重构的目标态与门禁约束，确保 bundle 退役、子流程拆分、Fail-Closed 与回退语义在设计和运行层面统一成立。

## Requirements

### Requirement: All ap-bundle Runtime Patterns Must Be Retired And Replaced By P5 Subprocess Library
所有 `ap-*-bundle` MUST 从目标态运行结构中移除，并由 P5 子流程库替代。

#### Scenario: Main processes no longer reference ap-bundle
- **WHEN** 迁移完成后检查 `development-process/full-development/hotfix/refactor`
- **THEN** `process.json` 中不得出现 `target_id=ap-*-bundle`
- **AND** 每个 phase 必须映射到已定义 P5/P6 子流程并契约闭合

### Requirement: Subprocess Decomposition Must Follow MECE And Pyramid Principle With Design-Pattern Constraints
子流程拆分 MUST 遵循 MECE、金字塔原理，并满足 SRP、DIP、LoD、组合复用约束。

#### Scenario: Decomposition design review catches overlap and leaking dependencies
- **WHEN** 子流程方案进入评审
- **THEN** 发现职责重叠、跨层依赖泄漏或多职责耦合必须判定 fail
- **AND** 不得进入实现阶段

### Requirement: Anti-Patterns Must Be Explicitly Defined And Enforced As Fail-Closed Conditions
流程拆分反例 MUST 落盘并作为 Fail-Closed 条件执行。

#### Scenario: Bundle-like mixed responsibility node is blocked
- **WHEN** 某子流程同时承担“需求归一+规格编排+发布打包”等混合职责
- **THEN** 门禁返回 fail-closed
- **AND** 要求按单一职责重新拆分

### Requirement: Every Phase Must Declare Rollback And Fail-Closed Path
每个 phase MUST 明确失败回退路径与阻断策略。

#### Scenario: Runtime failure triggers deterministic rollback
- **WHEN** 任一 phase 运行失败或证据不可达
- **THEN** 执行既定回退步骤并输出结构化失败记录
- **AND** 禁止静默跳转后续 phase

### Requirement: P1 Migration Matrix Must Be Complete And Executable
Phase1 迁移矩阵 MUST 覆盖全部 7 个待淘汰 bundle，且每行 MUST 含替代 ID、输入输出契约、调用方流程、迁移顺序、退役策略。

#### Scenario: Matrix completeness check passes
- **WHEN** 评审 `meta-gap-baseline.md` 中的 P1 迁移矩阵
- **THEN** 必须看到 `ap-001-002-003-bundle`、`ap-001-002-bundle`、`ap-003-004-bundle`、`ap-004-bundle`、`ap-006-bundle`、`ap-012-bundle`、`ap-013-014-015-017-bundle` 全量条目
- **AND** 每行字段完整且无 `TBD`/`待定`

### Requirement: Responsibility Overlap Must Be Explicitly Explained And Decoupled
若迁移矩阵出现一对多/多对多责任关系，MUST 提供“重叠解释 + 组合层解耦策略”，否则 MUST Fail-Closed。

#### Scenario: Overlap without decoupling explanation is blocked
- **WHEN** 审核到 AP 语义在多个替代流程中出现
- **THEN** 必须提供 profile 边界或组合解耦说明
- **AND** 若无说明，判定 Phase1 失败并阻断进入实现阶段

### Requirement: Bundle Must Not Be Described As Target-State Runtime Unit
bundle MUST NOT 在目标架构中被描述为运行时目标单元。

#### Scenario: Target-state architecture still references bundle is rejected
- **WHEN** `meta-processes.md`、`design.md` 或相关 spec 仍把 bundle 作为目标态 phase target
- **THEN** 评审结果必须为 fail
- **AND** 要求先完成目标态改写后再进入 P2
