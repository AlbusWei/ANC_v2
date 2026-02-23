---
name: "template-validator"
description: "在 lifecycle 与 registry handoff 前执行模板契约校验，统一输出可审计 gate 结论"
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

# template-validator

## Objective

对模板、schema 与目标资产进行一致性校验，确保进入 review 前已完成字段完整性、策略一致性和证据可追溯检查。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 新模板接入 | 提供模板与 schema 引用 | 结构化校验报告 | schema 不可达 |
| 资产进入 review 前 | 目标资产路径可读 | gate 决策与阻断问题列表 | 高风险问题未关闭 |
| 模板版本升级 | 新旧版本差异可比对 | 差异化风险报告 | 必填字段映射断裂 |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-meta-asset-quality-hardening
input_contract:
  format: json
  required:
    - template_ref
    - schema_ref
    - target_asset_ref
    - validation_profile
  validation:
    - template_ref must exist and be readable
    - schema_ref must resolve to canonical schema
    - target_asset_ref must exist and be readable
    - validation_profile must be explicit
output_contract:
  format: json
  required:
    - validation_report_ref
    - gate_decision
    - blocking_issues
  machine_judgement:
    - gate_decision is pass or fail
    - blocking_issues is non-empty when gate_decision is fail
    - validation report is traceable
fail_closed_rules:
  - template/schema/asset reference missing
  - required fields mismatch with no safe auto-fix
  - unresolved high-risk blocking issue
test_mount:
  test_doc: skills/meta/template-validator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `template_ref` | string | 指向可读取模板文件 | 文件不存在 |
| `schema_ref` | string | 指向规范 schema | 文件不存在或格式错误 |
| `target_asset_ref` | string | 指向待验资产 | 文件不存在 |
| `validation_profile` | string | 仅允许已定义 profile | profile 非法 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `validation_report_ref` | string | 指向报告文件或报告索引 | 路径可达检查 |
| `gate_decision` | string | 仅允许 `pass` 或 `fail` | 枚举校验 |
| `blocking_issues` | array | `fail` 时至少 1 项 | 规则校验 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| 关键引用缺失 | `missing_refs != []` | 阻断并返回缺失引用 | `2` |
| 字段不匹配 | `schema_mismatch=true` | 阻断并输出差异清单 | `2` |
| 高风险问题未解 | `high_risk_open > 0` | 阻断进入 review | `2` |
| 运行时异常 | 未捕获异常 | 中止并记录异常 | `1` |

## 运行命令

```bash
python3 skills/meta/template-validator/scripts/template_validator_runner.py \
  --input <input.json> \
  --output <output.json> \
  --report <report.json>
```

返回码约定：`0=success`，`2=fail-closed`，`1=unexpected error`。

## References

1. `skills/meta/template-validator/references/schema-map.md`
2. `skills/meta/template-validator/references/validation-policy.md`
