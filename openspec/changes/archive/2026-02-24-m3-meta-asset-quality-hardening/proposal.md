## Why

当前 `m3-self-development-e2e-online` 已进入 Session5/6 前阶段，但其流程资产中仍存在 `ap-*-bundle` 这类“语义不清、职责重叠、可维护性差”的中间层。该结构既不符合 AP 原子语义，也削弱了流程设计的可解释性与工程可复用性。

同时，Meta 资产（技能与流程）存在“结构可过、运行不强”的质量问题：

1. 若干 Meta 技能文档信息密度偏低，执行步骤与 Fail-Closed 策略不够可执行。
2. 多数流程缺少按 MECE 原则拆分的子流程库，导致 phase 语义与复用边界模糊。
3. 现有验证偏静态门禁，缺少以 openclaw 在线运行效果为准的主验收路径。

因此需要新建独立 change 做质量硬化，避免污染现有 Session5/6 E2E 节奏，并将整改结果作为其前置门禁依赖。

## What Changes

本 change `m3-meta-asset-quality-hardening` 聚焦三件事：

1. **流程架构重构**：淘汰所有 `ap-*-bundle`，改为 P5 子流程库（按 MECE + SRP + DIP + LoD + 组合复用设计）。
2. **Meta 资产质量升级**：统一升级 Meta 技能/流程资产，使其达到 `review` 准入质量（不推进 `active`）。
3. **验证策略升级**：确立 QA 在线运行测试为主验收，静态校验仅作为基础门禁。

## Capabilities

### New Capabilities

1. `meta-process-subflow-library`：面向 M3 的 P5 子流程可复用库，替代 bundle 方案。
2. `meta-runtime-qa-online-gate`：面向 Meta 资产的 openclaw 在线验证门禁。
3. `meta-asset-quality-gate-v1`：技能/流程统一质量量表与自动检查入口。

### Modified Capabilities

1. `m3-self-development`：从 bundle 调用迁移为 P5 子流程组合调用。
2. `meta.arch.agent-creator/process-creator/template-validator/skill-creator`：升级输入输出契约、执行手册与 Fail-Closed 决策。

## Impact

### Affected OpenSpec

1. `openspec/changes/m3-meta-asset-quality-hardening/*`
2. `openspec/changes/m3-self-development-e2e-online/tasks.md`（新增依赖约束）

### Affected Assets

1. `processes/meta/*`（重点：移除 bundle 引用并落地 P5 子流程）
2. `skills/meta/*` 与 `skills/skill-creator/*`
3. `tests/m3-self-development/*`（在线 QA 套件增强）

### Affected Governance

1. `docs/design/standards/*`（新增流程拆分方法论）
2. `docs/design/processes/*`、`docs/design/skills/*`、`docs/design/inventories/*`
3. `shared/registry/{process_registry.json,skill_registry.json}`
4. `docs/architecture/construction_plane.md`

### Lifecycle Constraint

1. 本 change 内所有新增/整改资产生命周期上限固定为 `review`。
2. 任意尝试推进 `active` 均视为 Fail-Closed。
