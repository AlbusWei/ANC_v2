# Skill 生命周期协议

> 版本: v0.2.0 | SSOT 上游: [system_overview.md](../../architecture/system_overview.md) §统一生命周期

## 概述

所有 Skill 遵循统一生命周期: `Draft → Review → Active → Deprecated → Retired`。本协议定义每个阶段的准入条件、操作和产出。

设计意图：

1. `draft` 允许快速迭代，但不允许越过能力契约门禁直接进入 `review`。
2. `review` 是“可治理”门槛，要求结构契约与能力契约同时成立。
3. `active` 是“可运行”门槛，要求测试证据完成并可追溯。

## 创建协议

### 前置条件

1. 有明确的 Objective（objective_ref）
2. 有 Spec（通过 spec-writer 生成或手动编写）
3. 有测试用例（通过 test-designer 生成或手动编写）

### 创建步骤

1. **资产创建**: 使用 skill-creator 或手动创建 SKILL.md + TEST.md
2. **能力契约写入**: 在 `SKILL.md` 中写入 `## Capability Contract (Machine-Readable)` + YAML 块
3. **模板校验**: 确认目录结构符合 skills/template/ 规范
4. **注册**: 在 skill_registry.json 添加条目（status: draft）
5. **Inventory 更新**: 在 skill-inventory.md 添加条目

### 产出

- `skills/{category}/{skill-name}/SKILL.md` — Skill 定义
- `skills/{category}/{skill-name}/TEST.md` — 测试用例（可选放 tests/）
- `skill_registry.json` 新条目
- `skill-inventory.md` 新条目

## 审查协议 (Draft → Review)

### 准入条件

- SKILL.md 完整（frontmatter + 所有必需节）
- Capability Contract YAML 块存在且可解析（固定标题 + `yaml` fenced block）
- Capability Contract 字段完整：`contract_version/objective_ref/input_contract/output_contract/fail_closed_rules/test_mount`
- TEST.md 存在且包含至少 1 个 P0 测试用例
- Registry 条目存在且字段完整
- SKILL.md frontmatter 与 registry 条目一致
- SKILL.md `test_mount` 与 registry `tests` 字段一致
- `python3 shared/registry/registry_contract_tool.py verify` 通过

### 审查内容

1. **architect**: 架构合规性（命名、层级、接口契约）
2. **qa**: 测试覆盖度（Objective 核心意图是否被覆盖）

### 产出

- 审查记录（通过/退回 + 原因）
- 状态转换: draft → review

## 激活协议 (Review → Active)

### 准入条件

- 审查通过（architect + qa）
- Smoke 级测试全部通过
- 无阻塞性问题

### 产出

- 状态转换: review → active
- Skill 可被 BPM 调度使用

## 废弃协议 (Active → Deprecated)

### 准入条件

- 有替代 Skill 或明确废弃原因
- 依赖方已迁移或有迁移计划
- admin 批准

## 退役协议 (Deprecated → Retired)

### 准入条件

- 无活跃依赖方
- 归档完成
- admin 批准

### 产出

- Registry 条目标记 retired
- 资产目录保留但不再维护
