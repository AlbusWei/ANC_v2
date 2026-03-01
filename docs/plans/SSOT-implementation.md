# SSOT Implementation — Superpower-Replacement + OpenJudge SDD/TDD Execution Plan

> Status: Active SSOT
> Last Updated: 2026-03-01
> Required Execution Skill: `superpowers:executing-plans`

## 1) 权威范围

本文件是该主题唯一实施真相（implementation SSOT）。

Supersedes:
- `docs/plans/archive/2026-02-27-m1-m3-gate-authenticity-implementation.md`
- `docs/plans/archive/2026-03-01-m4-m5-productized-lifecycle-implementation.md`
- `docs/plans/archive/2026-03-01-m4-m5-implementation-assets-plan.md`
- `docs/plans/archive/2026-03-01-m1-m3-m4-m5-executable-gap-closure-implementation.md`
- 所有依赖 OpenSpec 主链输入输出的历史实施结论

## 2) 总体执行策略

按 Batch 0 -> 4 线性推进，先改契约字段与流程，再替换技能执行入口，再完成 SDD/TDD 绑定与清理残留，最后统一回归与 SSOT 对账。

- Batch 0: 契约硬切（OpenSpec 字段移除）
- Batch 1: 技能替换（openspec-sync -> superpower-sync）
- Batch 2: SDD+TDD 绑定（superpower_ref 强制进入 gate）
- Batch 3: 主链残留清除（脚本/测试/校验器）
- Batch 4: 文档索引与 SSOT 收口验证

## 3) 执行任务（唯一有效任务集）

### Batch 0 — 契约硬切（流程与协议）

1. 修改 `processes/meta/construction-plane-governance/process.json`
   - `openspec_ref -> superpower_ref`
   - `openspec_sync_ref -> superpower_sync_ref`
   - p4 改为 `sync-superpower-state`
2. 修改 `processes/meta/construction-plane-governance/SKILL.md`
3. 修改 `processes/meta/construction-plane-governance/PROCESS.md`
4. 新增 `docs/design/interfaces/superpower-collaboration-protocol.md`
5. 新增 `docs/design/data-models/superpower-collaboration-schema.json`
6. 新增 `docs/design/processes/atomic/AP-035-superpower-round-sync.md`
7. 旧 openspec 协议相关文档标记 superseded 并从主链摘除引用

验证：
- `rg -n "openspec_ref|openspec_sync_ref" processes/meta/construction-plane-governance docs/design/interfaces docs/design/processes/atomic`
- 期望：主流程目标文件中无旧字段残留。

### Batch 1 — 技能替换（唯一执行入口）

1. 新增 `skills/system/superpower-sync/SKILL.md`
2. 新增 `skills/system/superpower-sync/TEST.md`
3. 新增 `skills/system/superpower-sync/scripts/superpower_sync.sh`
4. 更新 `processes/meta/construction-plane-governance/process.json` p4 `skill_id`
5. 更新 `shared/registry/skill_registry.json`（注册 superpower-sync，移除 openspec-sync 主链引用）
6. `skills/system/openspec-sync/*` 从主链引用移除（可归档，不可执行）

验证：
- `python3 shared/registry/registry_contract_tool.py verify`
- `rg -n "system.integration.openspec-sync" processes shared/registry docs/design/inventories`
- 期望：registry 校验通过；主链引用为 0。

### Batch 2 — SDD+TDD 硬绑定

1. 修改 `docs/design/modules/M1-openjudge-adapter-spec.md`
   - 输入契约加入 `superpower_ref` 必填
2. 修改 `docs/design/modules/M1-test-system.md`
   - 明确 `superpower_ref + TEST.md` 是 TDD 必需输入
3. 修改 `docs/design/skills/quality-gate-skills.md`
   - `evaluation-runner` 输入契约加入 `superpower_ref`
4. 修改 `docs/design/skills/self-development-skills.md`
   - SDD 输出契约补 `superpower_ref`
5. 修改 `docs/design/modules/M3-self-development.md`
   - 输入契约补 `superpower_ref` 必填
   - 输出契约补 `superpower_sync_ref` 与追溯约束
   - 验收矩阵去 OpenSpec 化（`M3-AC-05` 改为 superpower 会话工件校验）
6. 修改 `docs/design/modules/M4-lifecycle-management.md`
   - 切换为 `ProductVersionInstance` 治理语义
   - lifecycle-review 输入契约补 `superpower_ref`
7. 修改 `processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py`
   - 证据链校验加入 `superpower_ref` 可达性校验
8. 修改 `tests/m1-runtime/run_post_dev_regression.py`
   - 新增 `missing_superpower_ref -> fail-closed` 用例

验证：
- `python3 -m pytest tests/m1-runtime -q`
- `python3 tests/m1-runtime/run_post_dev_regression.py`
- 期望：缺 superpower_ref 场景 fail；其余链路保持可执行。

### Batch 3 — OpenSpec 主链残留清除

1. 修改 `shared/registry/registry_contract_tool.py`
   - 去掉 openspec 协同 schema 强制校验
   - 改为 superpower 协同 schema 强制校验
2. 修改 `tests/m6-governance/run_post_dev_regression.py`
3. 修改 `tests/m2-bpm-runtime/run_tc_full_dev_proc.py`
4. 修改 `skills/system/construction-audit/scripts/construction_audit.py`
5. 修改 `processes/meta/construction-plane-governance/scripts/run_round.py`
6. 修改 `processes/meta/construction-plane-governance/scripts/round_evidence_tool.py`

验证：
- `rg -n "openspec validate|openspec_ref|openspec_sync_ref" tests processes skills shared docs/design`
- 期望：主链目录不再依赖 openspec 主字段/主命令。

### Batch 4 — 索引与施工平面对账收口

1. 修改 `docs/design/inventories/process-inventory.md`
2. 修改 `docs/design/inventories/skill-inventory.md`
3. 修改 `docs/design/modules/module-dependency-matrix.md`
4. 修改 `docs/architecture/construction_plane.md`
5. 校验 `docs/plans/SSOT-design.md` 与本文件一致

验证：
- `python3 shared/registry/registry_contract_tool.py verify`
- `python3 tests/m6-governance/run_post_dev_regression.py`
- 全仓 grep 检查主链残留

## 4) DoD（完成定义）

1. 主流程字段中无 `openspec_ref/openspec_sync_ref`。
2. `system.integration.superpower-sync` 成为唯一施工协同同步技能入口。
3. M1 门禁对缺 `superpower_ref` 明确 fail-closed。
4. SDD 输出与 TDD 输入通过 `superpower_ref` 形成可追溯闭环。
5. registry 与关键回归套件通过。
6. SSOT、inventory、construction plane 同步完成且无漂移。

## 5) 执行纪律

1. 严格 TDD：先失败测试，再最小实现，再回归。
2. 每个 batch 完成后执行代码审查。
3. 不做兼容层，不保留双轨入口。
4. 不引入与本目标无关的重构。

## 6) 实施状态追踪

- Batch 0: pending
- Batch 1: pending
- Batch 2: pending
- Batch 3: pending
- Batch 4: pending

## 7) 变更日志

- 2026-03-01：重写为“Superpower 完全替代 OpenSpec + OpenJudge 驱动 SDD/TDD”的执行基线。
