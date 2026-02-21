# Skill Definition Standard

> 版本: v0.3.0 | 适用范围: meta/system/business skills

## 1. 目标

确保每个 Skill 同时满足：

1. 运行时可加载（Agent Skills/OpenClaw 兼容）
2. 能力可验证（Capability Contract 可机器校验）
3. 治理可追溯（Registry Contract 与测试引用闭环）

## 2. 分层契约模型（强制）

1. `Registry Contract`：注册、投影、状态门禁、路径可达性。
2. `Capability Contract`：技能能力声明、Fail-Closed 规则、测试挂载点。

约束：

1. `Registry Contract` 以 `shared/registry/*_registry.json` 的 `entry_contract` 为机器真相源。
2. `Capability Contract` 以 `SKILL.md` 正文中的固定 YAML 块为机器真相源。
3. `注册成功 != 能力合格`，两层都通过才允许进入后续生命周期。

## 3. SKILL.md 结构要求（强制）

1. frontmatter：保持 Agent Skills 最小兼容字段（`name/description/license/compatibility`）。
2. 正文必须包含固定标题：`## Capability Contract (Machine-Readable)`。
3. 标题下必须紧跟一个 `yaml` fenced block。

Capability Contract 最小必填字段：

1. `contract_version`（SemVer）
2. `objective_ref`
3. `input_contract`（至少包含 `format/required/validation`）
4. `output_contract`（至少包含 `format/required/machine_judgement`）
5. `fail_closed_rules`（非空列表）
6. `test_mount`（`test_doc/methodology_ref`）

## 4. 资产结构要求

1. `SKILL.md`（能力定义与机器契约）
2. `TEST.md`（建议位于 `tests/<skill-name>/TEST.md` 或 skill 内）
3. 可选 `references/`（复杂 schema 与补充材料）

## 5. 生命周期门禁要求

1. `draft -> review` 前必须通过 Capability Contract 解析与字段校验。
2. `review -> active` 前必须通过测试门禁并具备可追溯证据。
3. 任一层校验失败默认 Fail-Closed。

## 6. 与 Registry 咬合

1. `skill_registry.json` 必须记录 tests 路径并与 `SKILL.md` 的 `test_mount` 一致。
2. registry 中的 `agentskills` 快照必须与 `SKILL.md` frontmatter 一致。
3. 生命周期状态统一使用 5 态。

## 7. 验收条目

- [ ] `SKILL.md` frontmatter 可解析且兼容 Agent Skills
- [ ] Capability Contract YAML 块可解析且字段完整
- [ ] `test_mount` 路径可达并与 registry 一致
- [ ] registry 字段一致且通过 `registry_contract_tool.py verify`
- [ ] 失败规则可执行且可测试
