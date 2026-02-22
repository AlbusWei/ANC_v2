---
name: "skill-creator"
description: "Create or refactor ANC skills using the local standard template, including capability contract, test mount, registry patch plan, and lifecycle evidence pack"
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

# skill-creator

## Objective

用于新建或重构技能目录，确保技能可加载、可测试、可治理，并可推进 `draft -> review -> active`。

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
    - review_evidence_ref
    - smoke_evidence_ref
  machine_judgement:
    - generated frontmatter is parseable
    - capability contract fields are complete
    - test path is traceable and exists
    - registry patch plan includes required fields
fail_closed_rules:
  - required input fields missing
  - frontmatter cannot be parsed
  - capability contract invalid
  - test path not provided
  - registry patch incomplete
test_mount:
  test_doc: tests/skill-creator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  checklist: skills/skill-creator/references/checklist.md
  review_rubric: skills/skill-creator/references/review_rubric.md
  frontmatter_notes: skills/skill-creator/references/frontmatter_openclaw.md
  scaffold_script: skills/skill-creator/scripts/scaffold_skill.py
```

## Input Contract

- Format: markdown or json
- Required fields:
  - `skill_name`
  - `objective_ref`
  - `scope`
  - `constraints`
- Validation:
  - `skill_name` 必须使用 kebab-case
  - `constraints` 必须包含 Fail-Closed 与边界说明

## Output Contract

- Format: file layout + markdown
- Required fields:
  - `skills/<layer>/<namespace>/<skill-name>/SKILL.md`
  - `skills/<layer>/<namespace>/<skill-name>/TEST.md` 或 `tests/<skill-name>/TEST.md`
  - registry patch plan（`shared/registry/skill_registry.json`）
  - review/smoke evidence path

## Execution Steps

1. 对齐 `objective_ref` 与能力边界。
2. 按 `skills/template/SKILL.md` 生成或重构技能骨架。
3. 写入 `Capability Contract` 与执行步骤。
4. 补齐 `TEST.md`（至少 3 个 P0 场景：happy/fail-closed/traceability）。
5. 生成 registry patch plan 并对齐 `test_mount`。
6. 产出 review 证据与 smoke 证据。
7. 执行 `registry_contract_tool.py verify`。

最小脚手架命令：

```bash
python3 skills/skill-creator/scripts/scaffold_skill.py \
  --skill-name demo-skill \
  --layer system \
  --namespace qa \
  --objective-ref obj-demo \
  --output-root skills
```

## Fail-Closed Rules

- 关键输入缺失时直接失败并返回缺失项。
- frontmatter 不可解析时禁止继续。
- Capability Contract 不可解析或缺字段时禁止进入 review。
- 未提供测试路径时不允许推进生命周期。
- registry 校验失败时禁止交付。

## References

- 执行清单：`skills/skill-creator/references/checklist.md`
- Frontmatter 规则：`skills/skill-creator/references/frontmatter_openclaw.md`
- 评审量表：`skills/skill-creator/references/review_rubric.md`
