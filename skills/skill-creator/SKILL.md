---
name: "skill-creator"
description: "创建或更新技能资产，确保与 Objective->Spec->Test->Development 链路及 OpenClaw/Agent Skills 规范对齐。"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.1.0"
---

# skill-creator

用于新建或重构技能目录，确保技能可加载、可测试、可治理。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-phase0.5-skill-creator
input_contract:
  format: markdown_or_json
  required:
    - skill_name
    - objective_ref
    - scope
    - constraints
  validation:
    - skill_name must use kebab-case
    - objective_ref must be non-empty
    - constraints must include fail-closed behavior
output_contract:
  format: file_layout_and_markdown
  required:
    - skill_md_path
    - test_doc_path
    - registry_patch_plan
  machine_judgement:
    - generated frontmatter is parseable
    - test path is traceable and exists
    - registry patch plan includes required fields
fail_closed_rules:
  - required input fields missing
  - frontmatter cannot be parsed
  - test path not provided
test_mount:
  test_doc: tests/skill-creator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  checklist: skills/skill-creator/references/checklist.md
  review_rubric: skills/skill-creator/references/review_rubric.md
```

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
  - `skills/<skill-name>/SKILL.md`
  - `SKILL.md` 中的 `Capability Contract (Machine-Readable)` YAML 块
  - optional `skills/<skill-name>/references/*.md`
  - `tests/<skill-name>/TEST.md`
  - registry patch plan（skill_registry）
  - `registry_contract_tool.py verify` 通过证据

## Execution Steps

1. 明确技能目标、触发场景与边界。
2. 生成或更新 `SKILL.md` frontmatter 与核心步骤。
3. 写入 `Capability Contract (Machine-Readable)` YAML 块并完成字段校验。
4. 将长文档细节拆分到 `references/`。
5. 设计 `TEST.md`，覆盖 P0 目标和关键失败模式。
6. 同步更新 `skill_registry.json`，并确保 `test_mount` 与 registry `tests` 一致。
7. 执行 `python3 shared/registry/registry_contract_tool.py verify`。

## Fail-Closed Rules

- 关键输入缺失时直接失败并返回缺失项。
- frontmatter 不可解析时禁止继续。
- Capability Contract 不可解析或缺字段时禁止进入 `review`。
- 未提供测试路径时不允许标记为 active。
- `verify` 未通过时禁止交付。

## References

- 执行清单：`skills/skill-creator/references/checklist.md`
- Frontmatter 规则：`skills/skill-creator/references/frontmatter_openclaw.md`
- 评审量表：`skills/skill-creator/references/review_rubric.md`

## External References

- OpenClaw Skills: https://docs.openclaw.ai/tools/skills
- Agent Skills: https://agentskills.io/specification
