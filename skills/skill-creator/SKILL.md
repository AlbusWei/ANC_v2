---
name: "meta-skill-creator"
description: "创建或重构 Skill 资产，输出可直接进入 review 门禁的文档、测试与 registry 变更计划"
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

# meta-skill-creator

## Objective

在仓库内提供唯一的 Skill 资产生成入口，完成从输入契约到 `SKILL.md/TEST.md/registry` 计划的闭环，且对不完整输入执行 Fail-Closed。

## 命名与别名策略

1. 运行入口固定为 `meta-skill-creator`。
2. `skill-creator` 仅作为历史别名说明，仓库内禁止作为调用入口。
3. 稳定 `skill_id` 维持为 `meta.arch.skill-creator`，避免破坏既有 registry 追溯链。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 新建 Skill 资产 | `skill_name/layer/namespace/objective_ref` 完整 | 可审查的技能骨架与测试文档 | 关键字段缺失 |
| 重构既有 Skill | 已提供目标路径与重构边界 | 更新后的契约与测试计划 | 前后契约不一致 |
| 生命周期推进前审查 | 资产草案可读取 | registry patch 计划 + 证据路径 | test_mount 缺失 |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-meta-asset-quality-hardening
input_contract:
  format: json
  required:
    - skill_name
    - layer
    - namespace
    - objective_ref
  validation:
    - skill_name must be kebab-case
    - layer must be one of meta/system/business
    - namespace must be kebab-case compatible segment
    - objective_ref must be non-empty and traceable
output_contract:
  format: json
  required:
    - skill_md_path
    - test_doc_path
    - registry_patch_plan
    - review_evidence_ref
  machine_judgement:
    - generated frontmatter is parseable
    - capability contract fields are complete
    - test_mount path is reachable
    - registry patch includes required fields
fail_closed_rules:
  - missing mandatory input fields
  - invalid naming conventions
  - generated asset cannot satisfy review gate baseline
test_mount:
  test_doc: tests/skill-creator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  checklist: skills/skill-creator/references/checklist.md
  review_rubric: skills/skill-creator/references/review_rubric.md
  frontmatter_notes: skills/skill-creator/references/frontmatter_openclaw.md
  alias_policy: skills/skill-creator/references/alias-policy.md
  scaffold_output_spec: skills/skill-creator/references/scaffold-output-spec.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `skill_name` | string | kebab-case、语义稳定 | 为空或命名违规 |
| `layer` | string | `meta/system/business` | 枚举外取值 |
| `namespace` | string | kebab-case 分段 | 非法字符 |
| `objective_ref` | string | 非空且可追溯 | 空值 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `skill_md_path` | string | 指向生成的 `SKILL.md` | 文件存在性检查 |
| `test_doc_path` | string | 指向生成的 `TEST.md` | 文件存在性检查 |
| `registry_patch_plan` | object | 含 `skill_id/name/version/status/tests` | 结构化校验 |
| `review_evidence_ref` | string | 指向 review 证据路径 | 路径规则校验 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| 必要输入缺失 | `missing_fields != []` | 阻断并返回缺失字段 | `2` |
| 命名冲突 | 与保留名或非法名冲突 | 阻断并输出冲突详情 | `2` |
| 生成物不达标 | review 基线检查失败 | 阻断并返回失败项 | `2` |
| 运行时异常 | 未捕获异常 | 中止并输出异常摘要 | `1` |

## 运行命令

```bash
python3 skills/skill-creator/scripts/meta_skill_creator_runner.py \
  --input <input.json> \
  --output <output.json> \
  --report <report.json>
```

返回码约定：`0=success`，`2=fail-closed`，`1=unexpected error`。

## 补充命令（脚手架）

```bash
python3 skills/skill-creator/scripts/scaffold_skill.py \
  --skill-name <skill-name> \
  --layer <meta|system|business> \
  --namespace <namespace> \
  --objective-ref <objective-ref> \
  --description "<技能描述>" \
  --output-root skills
```

## References

1. `skills/skill-creator/references/checklist.md`
2. `skills/skill-creator/references/frontmatter_openclaw.md`
3. `skills/skill-creator/references/review_rubric.md`
4. `skills/skill-creator/references/alias-policy.md`
5. `skills/skill-creator/references/scaffold-output-spec.md`
