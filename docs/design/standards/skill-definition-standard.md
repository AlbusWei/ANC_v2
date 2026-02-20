# Skill Definition Standard

> 版本: v0.2.0 | 适用范围: meta/system/business skills

## 1. 目标

确保每个 Skill 都是可组合、可测试、可治理的最小能力单元。

## 2. 最小必填字段

1. `skill_id`
2. `name`
3. `owner`
4. `layer`
5. `input_contract`
6. `output_contract`
7. `fail_closed_rules`
8. `test_mount_point`

## 3. 资产结构要求

1. `SKILL.md`（Agent Skills 兼容）
2. `TEST.md`（建议位于 `/Users/albus/MyProjects/ANC_v2/tests/<skill-name>/TEST.md`）
3. 可选 `references/`

## 4. 契约规则

1. 输入契约必须声明 required 字段和校验策略。
2. 输出契约必须声明可机器判定字段。
3. 缺关键输入或输出不可解析时必须 Fail-Closed。

## 5. 与 Registry 咬合

1. `/Users/albus/MyProjects/ANC_v2/shared/registry/skill_registry.json` 必须镜像核心 frontmatter 字段。
2. 生命周期状态使用 5 态。
3. 任何 active skill 必须有可追溯测试入口。

## 6. 验收条目

- [ ] frontmatter 完整
- [ ] 测试入口可达
- [ ] registry 字段一致
- [ ] 失败规则可执行
