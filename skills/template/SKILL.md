---
name: "template-skill"
description: "ANC v2 skill template. Use this asset as the baseline when creating a new skill package."
license: "Apache-2.0"
compatibility: "openclaw>=0.0.0; agentskills>=0.2"
metadata: {"category":"template","owner":"architect","stability":"stable"}
allowed-tools: "Read Write Bash"
version: "0.1.0"
---

# template-skill

用于初始化新 Skill 的标准写法与结构约束。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-template-skill
input_contract:
  format: markdown
  required:
    - skill_name
    - objective_ref
    - scope
    - constraints
  validation:
    - skill_name must use kebab-case
    - objective_ref must be non-empty
    - constraints must declare prohibited behavior
output_contract:
  format: markdown_and_file_layout
  required:
    - skill_md
    - test_doc
    - registry_entry_plan
  machine_judgement:
    - capability contract block is parseable
    - frontmatter contains minimum required fields
    - test and registry references are traceable
fail_closed_rules:
  - required inputs missing
  - frontmatter parse failure
  - test/registry references missing
test_mount:
  test_doc: tests/template/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  agentskills_spec: skills/template/SKILL.md
```

## Objective

- 提供一个可被 Agent Skills/OpenClaw 识别的最小技能骨架。
- 保证新 Skill 在 `Objective -> Spec -> Test -> Development` 链路中可追溯。

## Input Contract

- Format: markdown
- Required fields:
  - skill_name
  - objective_ref
  - scope
  - constraints
- Validation:
  - `skill_name` 使用短横线命名
  - 明确禁止行为与失败回退策略

## Output Contract

- Format: markdown + file layout
- Required fields:
  - `SKILL.md`
  - optional `references/*`
  - optional `scripts/*`
- Validation:
  - frontmatter 字段完整且可解析
  - 输出路径可被 registry 记录

## Behavior Specification

1. 先定义触发条件与边界，再编写执行步骤。
2. 长文档知识放到 `references/`，`SKILL.md` 保持简洁。
3. 缺关键输入时 Fail-Closed，不生成不完整技能。

## Execution Steps

1. 澄清目标和输入契约。
2. 产出 frontmatter 与核心执行步骤。
3. 按需拆分 references/scripts。
4. 补齐测试用例并更新 registry。

## Constraints

- 不得跳过测试设计。
- 不得在未定义边界时输出“万能技能”。
- 不得生成与 SSOT 冲突的行为规范。

## Observability

- Evidence path: `tests/<skill-name>/TEST.md`
- Key metrics: template adoption rate, first-pass validation rate

## References

- 在这里存放技能相关的文档、参考网页url等。
- Agent Skills: https://agentskills.io/specification
- OpenClaw Skills: https://docs.openclaw.ai/tools/skills
