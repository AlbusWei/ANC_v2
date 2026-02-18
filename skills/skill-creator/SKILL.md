---
name: "skill-creator"
description: "创建或更新技能资产，确保与 Objective->Spec->Test->Development 链路及 OpenClaw/Agent Skills 规范对齐。"
license: "Apache-2.0"
compatibility: "openclaw>=0.0.0; agentskills>=0.2"
metadata: {"category":"meta","owner":"architect","stability":"draft"}
allowed-tools: "Read Write Bash"
version: "0.1.0"
---

# skill-creator

用于新建或重构技能目录，确保技能可加载、可测试、可治理。

## 何时使用

- 需要新建一个 Skill。
- 需要重构现有 Skill 的 frontmatter/结构。
- 需要补齐 Skill 与测试、registry 的一致性。

## Input Contract

- Format: markdown or json
- Required fields:
  - `skill_name`
  - `objective_ref`
  - `scope`
  - `constraints`
- Validation:
  - `skill_name` 必须使用短横线命名
  - 必须声明禁止行为与失败回退策略

## Output Contract

- Format: file layout + markdown
- Required fields:
  - `/Users/albus/MyProjects/ANC_v2/skills/<skill-name>/SKILL.md`
  - optional `/Users/albus/MyProjects/ANC_v2/skills/<skill-name>/references/*.md`
  - `/Users/albus/MyProjects/ANC_v2/tests/<skill-name>/TEST.md`
  - registry patch plan（skill_registry）

## Execution Steps

1. 明确技能目标、触发场景与边界。
2. 生成或更新 `SKILL.md` frontmatter 与核心步骤。
3. 将长文档细节拆分到 `references/`。
4. 设计 `TEST.md`，覆盖 P0 目标和关键失败模式。
5. 同步更新 `skill_registry.json`。

## Fail-Closed Rules

- 关键输入缺失时直接失败并返回缺失项。
- frontmatter 不可解析时禁止继续。
- 未提供测试路径时不允许标记为 active。

## References

- 执行清单：`/Users/albus/MyProjects/ANC_v2/skills/skill-creator/references/checklist.md`
- Frontmatter 规则：`/Users/albus/MyProjects/ANC_v2/skills/skill-creator/references/frontmatter_openclaw.md`
- 评审量表：`/Users/albus/MyProjects/ANC_v2/skills/skill-creator/references/review_rubric.md`

## External References

- OpenClaw Skills: https://docs.openclaw.ai/tools/skills
- Agent Skills: https://agentskills.io/specification
