# M4/M5 产品化生命周期治理 Implementation Plan

> Status: Superseded
> Superseded-By: `docs/plans/SSOT-implementation.md`
> Superseded-On: 2026-03-01

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 M4/M5 从“资产中心最小治理”升级为“内部产品中心 + 版本实例治理 + 混合触发自演化”并完成文档体系联动闭环。

**Architecture:** 以 Product 作为唯一治理语义单元，以 ProductVersionInstance（branch/worktree）作为 M4 生命周期治理对象；M5 通过周期+事件触发演化提案，编排到 M3 执行并经 M1 验证后回到 M4 放行。实现阶段先完成设计层、协议层、数据模型层与施工平面同步，不一次性引入重型运行时实现。

**Tech Stack:** Markdown 设计文档、JSON registry 合约校验、OpenSpec 校验、仓库内既有 verify 工具链（Python 3）。

---

### Task 1: 重写 M4 模块设计为“产品版本实例治理”

**Files:**
- Modify: `docs/design/modules/M4-lifecycle-management.md`
- Reference: `docs/plans/2026-03-01-m4-m5-productized-design.md`

**Step 1: 写“失败预期”检查（确认旧语义仍在）**

```bash
rg -n "资产|trigger_policy_manager|override-decision-recorder" docs/design/modules/M4-lifecycle-management.md
```

**Step 2: 运行检查确认当前仍是旧语义**

Run: `rg -n "资产|trigger_policy_manager|override-decision-recorder" docs/design/modules/M4-lifecycle-management.md`
Expected: 输出旧术语命中，证明需要重写。

**Step 3: 写最小新结构（产品中心）**

```markdown
## 模块定位
管理 ProductVersionInstance 的生命周期迁移、审批证据、版本角色切换。

## 核心对象
- Product
- ProductVersionInstance（主键：product_id + branch_or_worktree_id）
- ProductAssetBinding
- VersionRoleTag
```

**Step 4: 补充循环状态与多版本并存规则**

```markdown
生命周期循环：idea -> design -> build -> verify -> operate -> observe -> evolve -> design/build
治理终止：deprecate -> retire
并存规则：同一 product 可有多个实例并存，实例独立推进。
```

**Step 5: 运行文本检查确认新语义生效**

Run: `rg -n "ProductVersionInstance|多版本并存|生命周期循环" docs/design/modules/M4-lifecycle-management.md`
Expected: 命中新增关键语义。

**Step 6: Commit**

```bash
git add docs/design/modules/M4-lifecycle-management.md
git commit -m "docs: refactor M4 to product-version lifecycle governance"
```

---

### Task 2: 重写 M5 模块设计为“混合触发演化闭环”

**Files:**
- Modify: `docs/design/modules/M5-self-evolution.md`
- Reference: `docs/plans/2026-03-01-m4-m5-productized-design.md`

**Step 1: 写“失败预期”检查（确认缺少混合触发）**

```bash
rg -n "混合触发|周期触发|事件触发|EvolutionProposal" docs/design/modules/M5-self-evolution.md
```

**Step 2: 运行检查确认当前缺口**

Run: `rg -n "混合触发|周期触发|事件触发|EvolutionProposal" docs/design/modules/M5-self-evolution.md`
Expected: 关键字段缺失或不完整，证明需要补齐。

**Step 3: 写最小新结构（职责与边界）**

```markdown
## 模块定位
M5 负责演化提案生成与优先级治理，不替代 M3 执行与 M4 放行。

## 触发机制
- 周期触发（保底）
- 事件触发（插队）
```

**Step 4: 补充闭环路径与 fail-closed 规则**

```markdown
闭环：Monitor/Analyze -> Plan -> M3 Implement -> M1 Verify -> M4 Transition
Fail-Closed：证据缺失、指标不可比、未定义回滚时不得进入实施。
```

**Step 5: 运行文本检查确认新语义生效**

Run: `rg -n "混合触发|M3 Implement|M1 Verify|M4 Transition" docs/design/modules/M5-self-evolution.md`
Expected: 命中新增闭环语义。

**Step 6: Commit**

```bash
git add docs/design/modules/M5-self-evolution.md
git commit -m "docs: upgrade M5 to hybrid-trigger evolution loop"
```

---

### Task 3: 新增产品生命周期治理协议文档

**Files:**
- Create: `docs/design/interfaces/product-lifecycle-governance-protocol.md`
- Modify: `docs/design/README.md`

**Step 1: 写“失败预期”检查（确认协议未存在）**

```bash
test -f docs/design/interfaces/product-lifecycle-governance-protocol.md && echo "unexpected_exists" || echo "missing_expected"
```

**Step 2: 运行检查确认协议缺失**

Run: `test -f docs/design/interfaces/product-lifecycle-governance-protocol.md && echo "unexpected_exists" || echo "missing_expected"`
Expected: 输出 `missing_expected`。

**Step 3: 写最小协议结构**

```markdown
# Product Lifecycle Governance Protocol

## 协议对象
- Product
- ProductVersionInstance
- VersionRoleTag

## 关键接口
- create_product
- create_version_instance
- transition_version_state
- switch_version_role
- submit_evolution_proposal
```

**Step 4: 在 design README 索引中加入新协议入口**

```markdown
| `interfaces/` | ... + product lifecycle governance protocol |
```

**Step 5: 校验索引可检索**

Run: `rg -n "product-lifecycle-governance-protocol" docs/design/README.md docs/design/interfaces/product-lifecycle-governance-protocol.md`
Expected: 两个文件均命中。

**Step 6: Commit**

```bash
git add docs/design/interfaces/product-lifecycle-governance-protocol.md docs/design/README.md
git commit -m "docs: add product lifecycle governance protocol"
```

---

### Task 4: 新增产品生命周期数据模型文档

**Files:**
- Create: `docs/design/data-models/product-lifecycle-schemas.md`
- Modify: `docs/design/README.md`

**Step 1: 写“失败预期”检查（确认模型未存在）**

```bash
test -f docs/design/data-models/product-lifecycle-schemas.md && echo "unexpected_exists" || echo "missing_expected"
```

**Step 2: 运行检查确认缺失**

Run: `test -f docs/design/data-models/product-lifecycle-schemas.md && echo "unexpected_exists" || echo "missing_expected"`
Expected: 输出 `missing_expected`。

**Step 3: 写最小 schema 定义**

```markdown
## Product
required: product_id, goal, consumer, scope, acceptance, version_policy

## ProductVersionInstance
required: product_id, branch_or_worktree_id, state, role_tag, asset_bindings

## EvolutionProposal
required: proposal_id, trigger_type, target_product_id, expected_value, rollback_plan
```

**Step 4: 更新 design README 索引到 data-models**

```markdown
| `data-models/` | ... + product lifecycle schemas |
```

**Step 5: 校验模型文档可检索**

Run: `rg -n "ProductVersionInstance|EvolutionProposal|version_policy" docs/design/data-models/product-lifecycle-schemas.md`
Expected: 命中模型关键字段。

**Step 6: Commit**

```bash
git add docs/design/data-models/product-lifecycle-schemas.md docs/design/README.md
git commit -m "docs: add product lifecycle schema definitions"
```

---

### Task 5: 同步模块依赖矩阵与施工平面

**Files:**
- Modify: `docs/design/modules/module-dependency-matrix.md`
- Modify: `docs/architecture/construction_plane.md`

**Step 1: 写“失败预期”检查（确认缺少产品中心表述）**

```bash
rg -n "产品中心|版本实例|混合触发|M4.*M5" docs/design/modules/module-dependency-matrix.md docs/architecture/construction_plane.md
```

**Step 2: 运行检查确认需补齐**

Run: `rg -n "产品中心|版本实例|混合触发|M4.*M5" docs/design/modules/module-dependency-matrix.md docs/architecture/construction_plane.md`
Expected: 命中不足或语义不完整。

**Step 3: 更新依赖矩阵中的 M4/M5 行描述**

```markdown
M4: 版本实例治理（ProductVersionInstance）
M5: 周期+事件触发演化（EvolutionProposal）
关键路径：(M3 + M4) -> M5 -> M3
```

**Step 4: 在施工平面新增 M4/M5 产品化升级任务条目**

```markdown
- [ ] M4/M5 产品化治理设计落地（产品中心 + 多版本并存 + 混合触发）
```

**Step 5: 校验同步结果**

Run: `rg -n "ProductVersionInstance|混合触发|产品化治理" docs/design/modules/module-dependency-matrix.md docs/architecture/construction_plane.md`
Expected: 两文件命中关键项。

**Step 6: Commit**

```bash
git add docs/design/modules/module-dependency-matrix.md docs/architecture/construction_plane.md
git commit -m "docs: sync dependency matrix and construction plane for M4/M5 productization"
```

---

### Task 6: 同步 process/agent/skill inventory 与 registry 无漂移校验

**Files:**
- Modify: `docs/design/inventories/process-inventory.md`
- Modify: `docs/design/inventories/agent-inventory.md`
- Modify: `docs/design/inventories/skill-inventory.md`
- Validate: `shared/registry/process_registry.json`
- Validate: `shared/registry/agent_directory.json`
- Validate: `shared/registry/skill_registry.json`

**Step 1: 在 inventory 增加 M4/M5 产品化语义联动备注**

```markdown
## M4/M5 产品化联动备注（2026-03-01）
- 生命周期治理对象升级为 ProductVersionInstance。
- 资产维度保持 registry 5 态，不新增强制字段。
- 本回合 registry 为 no-delta（若无新增资产）。
```

**Step 2: 运行 registry 合约校验**

Run: `python3 shared/registry/registry_contract_tool.py verify`
Expected: 校验通过，无 schema/contract 报错。

**Step 3: 运行关键词对账检查**

Run: `rg -n "ProductVersionInstance|产品化联动备注" docs/design/inventories`
Expected: 三份 inventory 均可检索到联动备注或引用。

**Step 4: Commit**

```bash
git add docs/design/inventories/process-inventory.md docs/design/inventories/agent-inventory.md docs/design/inventories/skill-inventory.md
git commit -m "docs: align inventories with M4/M5 product-centered governance semantics"
```

---

### Task 7: 端到端文档与规范验收

**Files:**
- Validate: `docs/design/modules/M4-lifecycle-management.md`
- Validate: `docs/design/modules/M5-self-evolution.md`
- Validate: `docs/design/interfaces/product-lifecycle-governance-protocol.md`
- Validate: `docs/design/data-models/product-lifecycle-schemas.md`
- Validate: `docs/architecture/construction_plane.md`

**Step 1: 运行 OpenSpec 校验**

Run: `openspec validate --all`
Expected: 校验通过；若失败，按报错补齐变更说明。

**Step 2: 运行模块联动关键字检查**

Run: `rg -n "ProductVersionInstance|混合触发|版本并存|evolve" docs/design/modules docs/design/interfaces docs/design/data-models docs/architecture`
Expected: 关键目录均命中，且语义一致。

**Step 3: 运行最小发布隔离与 registry 校验（文档回合）**

Run:
- `python3 shared/registry/registry_contract_tool.py verify`
- `python3 tools/release/release_isolation_gate.py`

Expected: 校验通过，无私有资产泄漏与 registry 不一致。

**Step 4: 汇总验收结论（自然语言）**

```markdown
结论需包含：
- 目标是否达成
- M4/M5 新边界是否清晰
- 风险与后续实现阶段待办
```

**Step 5: Commit**

```bash
git add docs/design/modules/M4-lifecycle-management.md docs/design/modules/M5-self-evolution.md docs/design/interfaces/product-lifecycle-governance-protocol.md docs/design/data-models/product-lifecycle-schemas.md docs/design/inventories/process-inventory.md docs/design/inventories/agent-inventory.md docs/design/inventories/skill-inventory.md docs/design/modules/module-dependency-matrix.md docs/architecture/construction_plane.md docs/design/README.md
git commit -m "docs: complete M4/M5 productized lifecycle and self-evolution design baseline"
```
