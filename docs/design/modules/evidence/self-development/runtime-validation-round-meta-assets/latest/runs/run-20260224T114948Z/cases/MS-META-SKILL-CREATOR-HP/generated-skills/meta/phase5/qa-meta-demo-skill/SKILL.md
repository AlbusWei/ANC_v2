---
name: "qa-meta-demo-skill"
description: "Phase5 online QA demo skill"
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

# qa-meta-demo-skill

## Objective

围绕 `obj-m3-meta-asset-quality-hardening` 提供可执行能力，并确保输入约束、输出契约与 Fail-Closed 行为可测试、可追溯。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 新建资产 | 关键输入齐全 | 产出符合标准的技能文档与测试文档 | 关键字段缺失 |
| 重构资产 | 变更范围明确 | 更新契约并同步测试 | 约束冲突 |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-meta-asset-quality-hardening
input_contract:
  format: json
  required:
    - primary_input
  validation:
    - primary_input must be non-empty
output_contract:
  format: markdown_or_json
  required:
    - primary_output
  machine_judgement:
    - output includes required fields
fail_closed_rules:
  - missing required input fields
  - output contract validation failed
test_mount:
  test_doc: docs/design/modules/evidence/self-development/runtime-validation-round-meta-assets/latest/runs/run-20260224T114948Z/cases/MS-META-SKILL-CREATOR-HP/generated-skills/meta/phase5/qa-meta-demo-skill/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `primary_input` | string/object | 非空且可解析 | 空值或不可解析 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `primary_output` | string/object | 满足 output_contract 定义 | 结构化校验 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| 输入缺失 | `missing_fields != []` | 阻断并返回缺失字段 | `2` |
| 契约不满足 | `contract_valid=false` | 阻断并返回失败项 | `2` |
| 运行时异常 | 未捕获异常 | 中止并输出异常摘要 | `1` |

## 运行命令

```bash
# 根据实际技能补充运行命令；无 runner 时给出文档化门禁命令。
python3 shared/registry/registry_contract_tool.py verify
```
