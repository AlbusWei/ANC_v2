# SSOT Design — Superpower + OpenJudge SDD/TDD Governance (OpenSpec Removed)

> Status: Active SSOT
> Last Updated: 2026-03-01
> Scope: Superpower 协同契约 + OpenJudge 执行门禁 + M1/M3/M4/M5/M6 联动

## 1) 权威范围

本文件是该主题唯一设计真相（design SSOT）。

Supersedes:
- `docs/plans/archive/2026-02-27-m1-m3-gate-authenticity-design.md`
- `docs/plans/archive/2026-03-01-m4-m5-productized-design.md`
- `docs/plans/archive/2026-03-01-m1-m3-m4-m5-executable-gap-closure-design.md`
- 所有以 OpenSpec 为主协同入口的历史设计结论

## 2) 背景与问题

当前体系虽然已具备 M1 OpenJudge 适配与质量门禁能力，但在协同契约层仍存在 OpenSpec 依赖，导致：

1. 协同契约源不唯一（Superpower 与 OpenSpec 并存）。
2. SDD 产物与 TDD 门禁输入未被同一契约主键绑定。
3. 施工回合（M6）在 process/skill/schema 层仍以 OpenSpec 字段为必填，形成语义与执行漂移。

本轮目标是**完全移除 OpenSpec 主链依赖**，以 Superpower 作为唯一协同与决策契约层，并通过 M1(OpenJudge) 实现可执行 TDD 门禁。

## 3) 目标终态架构

唯一主链：

`Superpower Contract -> M3(SDD execution) -> M1(OpenJudge TDD Gate) -> M2(runtime state) -> M4(lifecycle governance)`

### 3.1 各层职责

1. Superpower：唯一设计/计划/决策协同契约源（替代 OpenSpec）。
2. M3：按 superpower 契约实施开发（SDD 执行层）。
3. M1：使用 OpenJudge 作为评测执行内核，输出统一 gate verdict（TDD 门禁层）。
4. M2：运行态状态机与过程治理。
5. M4：产品版本实例生命周期状态迁移与角色切换。

### 3.2 强制输入绑定

1. SDD 运行上下文必须产出 `superpower_ref`。
2. TDD 门禁必须消费 `superpower_ref + TEST.md 编译产物 + actual outputs`。
3. 若 `superpower_ref` 缺失、不可解析或不可追溯，门禁默认 fail-closed。

## 4) 关键设计决策（Decision Baseline）

### D1. 完全替代（No Compatibility）
OpenSpec 不保留兼容路径，不再作为主流程输入/输出字段、门禁验证命令、回合同步协议来源。

### D2. 协同契约单源
Superpower 是唯一协同契约源；任何流程输入中的协同引用字段统一为 `superpower_ref`。

### D3. 同步记录单源
施工治理回合同步输出统一为 `superpower_sync_ref`；旧 `openspec_sync_ref` 语义废止。

### D4. SDD+TDD 联动硬约束
SDD 的交付必须可被 TDD 门禁反查；缺失 SDD 契约上下文的 TDD 请求一律拒绝。

### D5. OpenJudge 角色固定
OpenJudge 仅负责 raw eval 执行，M1 adapter 负责 unified verdict 与 gate_decision 归一。

### D6. Fail-Closed 默认策略
证据缺失、契约缺失、判定不可解析、指标不可比、回滚缺失、非法迁移均阻断。

### D7. 最小可执行与可审计
优先保证“可执行闭环 + 可追溯证据 + 阻断真实生效”，再考虑优化与扩展。

## 5) 资产级设计改造范围

### 5.1 必改流程资产

1. `processes/meta/construction-plane-governance/process.json`
   - `openspec_ref -> superpower_ref`
   - `openspec_sync_ref -> superpower_sync_ref`
   - p4 phase 改为 `sync-superpower-state`
2. `processes/meta/construction-plane-governance/SKILL.md`
3. `processes/meta/construction-plane-governance/PROCESS.md`

### 5.2 必改技能资产

1. 新增 `skills/system/superpower-sync/*`
2. 从主链移除 `skills/system/openspec-sync/*` 引用

### 5.3 必改接口/模型资产

1. 新增 `docs/design/interfaces/superpower-collaboration-protocol.md`
2. 新增 `docs/design/data-models/superpower-collaboration-schema.json`
3. 新增 `docs/design/processes/atomic/AP-035-superpower-round-sync.md`
4. 旧 openspec 协同协议、schema、AP 标记 superseded 并摘除主链引用

### 5.4 必改 SDD/TDD 门禁资产

1. `docs/design/modules/M1-openjudge-adapter-spec.md`
2. `docs/design/modules/M1-test-system.md`
3. `docs/design/skills/quality-gate-skills.md`
4. `docs/design/skills/self-development-skills.md`
5. `processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py`
6. `tests/m1-runtime/run_post_dev_regression.py`

### 5.5 必改治理与验证资产

1. `shared/registry/registry_contract_tool.py`
2. `tests/m6-governance/run_post_dev_regression.py`
3. `tests/m2-bpm-runtime/run_tc_full_dev_proc.py`
4. `skills/system/construction-audit/scripts/construction_audit.py`
5. `processes/meta/construction-plane-governance/scripts/run_round.py`
6. `processes/meta/construction-plane-governance/scripts/round_evidence_tool.py`

### 5.6 必改索引与施工平面资产

1. `docs/design/inventories/process-inventory.md`
2. `docs/design/inventories/skill-inventory.md`
3. `docs/design/modules/module-dependency-matrix.md`
4. `docs/architecture/construction_plane.md`

## 6) In Scope / Out of Scope

### In Scope

1. OpenSpec -> Superpower 完全替代（主链字段、流程、技能、校验）。
2. SDD 与 TDD 的契约主键绑定（`superpower_ref`）。
3. M1 门禁对缺 `superpower_ref` 的 fail-closed。
4. M6 施工回合同步记录与 schema 改造。

### Out of Scope（本轮）

1. 新增复杂平台服务层。
2. 非必要 UI 层治理界面。
3. 与当前主题无关的模块重构。

## 7) 验收设计口径

1. 主流程中不存在 `openspec_ref/openspec_sync_ref`。
2. `system.integration.superpower-sync` 成为唯一回合同步技能入口。
3. M1 gate 对缺 `superpower_ref` 请求 fail-closed。
4. SDD 输出和 TDD 输入通过 `superpower_ref` 可追溯绑定。
5. registry 与回归验证通过，且无 OpenSpec 主链依赖残留。

## 8) 设计变更日志

- 2026-03-01：重写为“Superpower 完全替代 OpenSpec”的单源设计基线。
