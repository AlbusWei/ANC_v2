---
name: "spec-writer"
description: "将 Objective 固化为可执行 Spec，明确 I/O 契约、验收条款、风险与回退边界"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.3.0"
---

# spec-writer

## Objective

把目标需求转化为工程可执行规范，确保后续测试、开发、回滚均有明确约束与可验证条款。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 新 Objective 进入 Spec 阶段 | 已有 `objective_ref` 与约束 | 结构化 Spec 草案 | 关键约束缺失 |
| 需求变更触发 Spec 更新 | 变更影响面已评估 | 更新版 Spec + 风险条款 | 验收条款不可测试 |
| 交付前审查 | Spec 已完成初稿 | 评审版 Spec 文档 | 与 SSOT 冲突 |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-meta-asset-quality-hardening
input_contract:
  format: json
  required:
    - objective_ref
    - problem_statement
    - constraints
  validation:
    - objective_ref must be resolvable
    - problem_statement must include explicit gap
    - constraints must include fail-closed boundary
output_contract:
  format: markdown
  required:
    - scope
    - input_contract
    - output_contract
    - acceptance_criteria
    - risks
    - rollback_strategy
  machine_judgement:
    - required sections are present
    - acceptance_criteria are testable
    - rollback strategy is executable
fail_closed_rules:
  - missing required input fields
  - acceptance criteria not testable
  - spec conflicts with architecture/process SSOT
test_mount:
  test_doc: skills/meta/spec-writer/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `objective_ref` | string | 必须可追溯到 Objective | 无法解析 |
| `problem_statement` | string | 明确问题与目标差距 | 语义空泛 |
| `constraints` | array/object | 含不可违背约束与边界 | 关键约束缺失 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `scope` | section | 同时含 in-scope/out-of-scope | 结构校验 |
| `acceptance_criteria` | section | 每条可映射测试用例 | 人审 + 规则匹配 |
| `risks` | section | 至少含风险等级与处置策略 | 结构校验 |
| `rollback_strategy` | section | 包含触发条件与回退步骤 | 可执行性检查 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| 输入缺失 | `missing_fields != []` | 阻断并返回缺失字段 | `2` |
| 验收条款不可测 | `untestable_criteria > 0` | 阻断并要求重写条款 | `2` |
| SSOT 冲突 | `ssot_conflict=true` | 阻断并标注冲突项 | `2` |
| 运行时异常 | 未捕获异常 | 中止并输出异常摘要 | `1` |

## 运行命令

```bash
# spec-writer 为文档化技能，无独立 runner。
# 建议在产出后执行以下门禁：
python3 shared/registry/registry_contract_tool.py verify
```

## References

1. `skills/meta/spec-writer/references/spec-template.md`
2. `skills/meta/spec-writer/references/constraint-examples.md`
