---
name: "template-skill"
description: "ANC skill template for creating standards-compliant skills with capability contract, fail-closed rules, and traceable test mount"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.2.0"
---

# template-skill

## Objective

提供一个符合 ANC 标准的技能模板，覆盖 frontmatter、Capability Contract、Fail-Closed 与测试挂载点。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-template-skill
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
  format: markdown_and_file_layout
  required:
    - skill_md_path
    - test_doc_path
    - registry_patch_plan
  machine_judgement:
    - frontmatter contains name/description/license/compatibility
    - capability contract yaml is parseable
    - test_mount is present and traceable
fail_closed_rules:
  - required inputs missing
  - frontmatter parse failure
  - capability contract missing required fields
  - test mount path missing
test_mount:
  test_doc: tests/template/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  template_checklist: skills/template/references/template-checklist.md
  smoke_script: skills/template/scripts/smoke_template_skill.py
```

## Input Contract

- Format: markdown or json
- Required fields:
  - `skill_name`
  - `objective_ref`
  - `scope`
  - `constraints`

## Output Contract

- Format: markdown + file layout
- Required fields:
  - `SKILL.md`
  - `TEST.md`
  - registry patch plan (when non-template skill)

## Execution Steps

1. 先写 frontmatter（`name/description/license/compatibility`）。
2. 写 `Capability Contract (Machine-Readable)` 固定标题与 YAML 块。
3. 明确 Input/Output/Fail-Closed/Execution Steps。
4. 绑定 `test_mount` 与 methodology。
5. 运行 smoke 脚本检查模板最小结构。

最小执行命令：

```bash
python3 skills/template/scripts/smoke_template_skill.py \
  --skill-file skills/template/SKILL.md \
  --test-file tests/template/TEST.md
```

## Fail-Closed Rules

- 缺关键 frontmatter 字段立即失败。
- 缺 Capability Contract 或必填字段立即失败。
- 缺 `test_mount` 立即失败。

## References

- 模板检查清单：`skills/template/references/template-checklist.md`
