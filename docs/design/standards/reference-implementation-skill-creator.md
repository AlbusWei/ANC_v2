# Reference Implementation: meta-skill-creator

> 版本: v0.3.0 | 参考对象: `skills/skill-creator/SKILL.md`

## 1. 目的

将 `meta-skill-creator` 作为标准实现样板，定义“从 Objective 到可治理 Skill 资产”的最小闭环，并明确历史别名治理策略。

## 2. 样板覆盖点

1. 触发矩阵与字段级输入/输出契约。
2. Capability Contract 机器块（固定标题 + YAML）。
3. Fail-Closed 决策表与返回码契约（`0/2/1`）。
4. 标准化测试挂载点（6 用例结构）。
5. registry patch 计划与生命周期门禁。
6. 运行名治理：`meta-skill-creator`（唯一入口）+ `skill-creator`（历史别名说明）。

## 3. 推荐执行步骤

1. 明确 `skill_name/layer/namespace/objective_ref`。
2. 使用 runner 执行脚手架生成：
   - `python3 skills/skill-creator/scripts/meta_skill_creator_runner.py --input <json> --output <json> [--report <json>]`
3. 校验生成产物是否满足 review gate 基线（无 `TODO` 占位、契约字段完整）。
4. 生成并审阅 registry patch 计划。
5. 执行 `python3 shared/registry/registry_contract_tool.py verify`。
6. 通过后推进 `draft -> review`。

## 4. 质量门禁

1. frontmatter 可解析且运行名为 `meta-skill-creator`。
2. Capability Contract 可解析且字段完整。
3. 测试文档满足 6 用例结构（含 2 个 Fail-Closed + 1 个 Traceability）。
4. registry path 与 tests 路径可达。
5. 别名策略文档存在并明确“旧名禁用调用”。

## 5. 常见反模式

1. 仍使用 `skill-creator` 作为运行调用名。
2. 只生成 `SKILL.md`，未同步 `TEST.md` 与 registry 计划。
3. 保留 `TODO` 占位导致生成物不可直接进入 review。
4. 未执行 registry verify 即宣称生命周期可推进。
