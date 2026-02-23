# 元技能清单与设计

> 版本: v0.4.0 | 分类: Meta Skills | 层级: L1 | 最后更新: 2026-02-23

## 已有元技能

1. `meta.qa.llm-judge`
2. `meta.arch.spec-writer`
3. `meta.qa.test-designer`
4. `meta.arch.skill-creator`（运行名：`meta-skill-creator`；`skill-creator` 仅历史别名）
5. `meta.arch.objective-writer`
6. `meta.arch.agent-creator`
7. `meta.arch.process-creator`
8. `meta.arch.template-validator`

M3 自开发技能设计包：

- `docs/design/skills/self-development-skills.md`

## 生命周期

统一 5 态：`draft -> review -> active -> deprecated -> retired`

## 本轮治理约束（Phase4 联动口径）

1. 上述 8 个技能在本回合统一推进到 `review`（不推进 `active`）。
2. `meta.arch.skill-creator` 稳定 `skill_id` 不变，仓库内运行入口仅允许 `meta-skill-creator`。
3. `skill-creator` 仅保留历史别名说明，不得作为仓库内调用指令。
4. 每个技能必须具备执行级 `SKILL.md`、标准化测试文档与 references 支撑。
5. `shared/registry/skill_registry.json` 在 Phase4 仅执行一致性核对，无字段差异（no-delta）。
