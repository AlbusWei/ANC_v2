---
name: "test-designer"
description: "基于 Objective 与 Spec 设计测试用例，确保测试资产可直接驱动 TDD 与门禁判定"
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

# test-designer

## Objective

把 Objective 与 Spec 约束映射成可执行测试设计，覆盖主链路、异常链路、回退链路与证据链条。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 新 Spec 进入开发前 | `objective_ref/spec_ref/risk_focus` 完整 | 标准化测试设计文档 | P0 场景缺失 |
| 缺陷回归补测 | 已识别缺陷与回归范围 | 回归增量用例集 | 缺陷与用例不可追溯 |
| 生命周期审查 | 测试文档初稿可读 | 评审级测试资产 | evaluation 配置缺失 |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-meta-asset-quality-hardening
input_contract:
  format: json
  required:
    - objective_ref
    - spec_ref
    - risk_focus
  validation:
    - objective_ref must be resolvable
    - spec_ref must point to an existing spec
    - risk_focus must include at least one P0 scenario
output_contract:
  format: markdown
  required:
    - objective_alignment
    - test_cases
    - evaluation_config
    - traceability_map
  machine_judgement:
    - every critical spec clause has test coverage
    - fail-closed scenarios are explicitly designed
    - evaluation configuration is executable
fail_closed_rules:
  - missing objective_ref or spec_ref
  - no P0 scenario in designed test cases
  - traceability map cannot map to source spec
test_mount:
  test_doc: skills/meta/test-designer/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `objective_ref` | string | 必须可追溯到 Objective | 无法解析 |
| `spec_ref` | string | 指向现行 Spec | 路径不可达 |
| `risk_focus` | array | 至少 1 个 P0 场景 | 不含 P0 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `objective_alignment` | section | 明确目标到用例映射 | 人审 + 规则匹配 |
| `test_cases` | section | 含 happy/fail-closed/traceability | 结构检查 |
| `evaluation_config` | section | 轮次、视角、超时明确 | 字段检查 |
| `traceability_map` | section | 可映射到 spec 条款 | 可追溯性检查 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| 引用缺失 | `missing_refs != []` | 阻断并返回缺失引用 | `2` |
| P0 场景缺失 | `p0_count == 0` | 阻断并要求补齐 | `2` |
| 追溯图断裂 | `traceability_broken=true` | 阻断并返回断点 | `2` |
| 运行时异常 | 未捕获异常 | 中止并记录异常 | `1` |

## 运行命令

```bash
# test-designer 为文档化技能，无独立 runner。
# 建议在产出后执行以下门禁：
python3 shared/registry/registry_contract_tool.py verify
```

## References

1. `skills/meta/test-designer/references/test-case-patterns.md`
2. `skills/meta/test-designer/references/evaluation-config-profiles.md`
