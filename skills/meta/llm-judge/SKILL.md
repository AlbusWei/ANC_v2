---
name: "llm-judge"
description: "基于 Objective/Spec 对输出进行结构化评判，给出可执行 verdict 与改进建议"
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

# llm-judge

## Objective

为质量门禁提供可结构化消费的评审结果，确保 verdict、置信度、证据链和整改建议都可复核与复现。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 测试执行后判定 | Objective/Spec/输出证据可读 | 结构化 verdict | 输入证据缺失 |
| 回归复测 | 缺陷与期望条件已定义 | 差异化复测结论 | 判定依据不完整 |
| 发布前总门禁 | 全量测试结果可读取 | 最终裁决建议 | 关键输入不可解析 |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-meta-asset-quality-hardening
input_contract:
  format: json
  required:
    - objective
    - spec_ref
    - expected_conditions
    - actual_output_ref
  validation:
    - objective must be non-empty
    - spec_ref must be resolvable
    - expected_conditions must be a non-empty list
    - actual_output_ref must be resolvable
output_contract:
  format: json
  required:
    - pass
    - confidence
    - remarks
    - suggestions
    - traceability
  machine_judgement:
    - output must be valid json
    - pass must be boolean
    - confidence must be number in [0, 1]
    - traceability must map to objective/spec evidence
fail_closed_rules:
  - missing critical input fields
  - unresolved actual output reference
  - verdict payload invalid or non-parseable
test_mount:
  test_doc: skills/meta/llm-judge/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `objective` | string | 非空且可解释 | 空值 |
| `spec_ref` | string | 指向可读取 spec | 不可解析 |
| `expected_conditions` | array | 非空且可验证 | 空数组 |
| `actual_output_ref` | string | 指向可读取输出证据 | 不可解析 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `pass` | boolean | true/false | 类型校验 |
| `confidence` | number | 0 到 1 | 范围校验 |
| `remarks` | string/array | 明确判定依据 | 非空校验 |
| `suggestions` | array | fail 时至少 1 条可执行建议 | 条件校验 |
| `traceability` | object | 包含证据路径和来源映射 | 结构化校验 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| 输入字段缺失 | `missing_fields != []` | 阻断并返回缺失字段 | `2` |
| 证据不可读 | `unresolvable_refs != []` | 阻断并返回不可读证据 | `2` |
| verdict 不可解析 | JSON 校验失败 | 阻断并标记无效结果 | `2` |
| 运行时异常 | 未捕获异常 | 中止并记录异常 | `1` |

## 运行命令

```bash
# llm-judge 为文档化技能，无独立 runner。
# 建议在产出后执行以下门禁：
python3 shared/registry/registry_contract_tool.py verify
```

## References

1. `skills/meta/llm-judge/references/verdict-schema.md`
2. `skills/meta/llm-judge/references/judge-policy.md`
