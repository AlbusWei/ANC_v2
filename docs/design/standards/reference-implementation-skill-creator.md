# Reference Implementation: skill-creator

> 版本: v0.2.0 | 参考对象: `/Users/albus/MyProjects/ANC_v2/skills/skill-creator/SKILL.md`

## 1. 目的

将 `skill-creator` 作为标准实现样板，定义“从 Objective 到可治理 Skill 资产”的最小闭环。

## 2. 样板覆盖点

1. 输入契约定义
2. 输出资产布局
3. Fail-Closed 规则
4. 测试挂载点
5. registry 同步要求

## 3. 推荐执行步骤

1. 明确 `skill_name`、`objective_ref`、边界约束。
2. 生成或更新 `SKILL.md`。
3. 生成测试文档 `/Users/albus/MyProjects/ANC_v2/tests/<skill-name>/TEST.md`。
4. 生成 registry patch plan。
5. 触发 lifecycle-review 进入 review 状态。

## 4. 质量门禁

- 必须有 P0 用例
- frontmatter 可解析
- registry path 可达
- fail 模式可说明

## 5. 常见反模式

1. 只写 SKILL，不写测试。
2. 测试与 output contract 不一致。
3. registry 未更新即宣称 active。
