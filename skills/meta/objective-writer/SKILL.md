---
name: "objective-writer"
description: "将原始需求归一为可执行 Objective 契约，输出可直接进入 Spec/Test 阶段的目标基线"
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

# objective-writer

## Objective

把业务诉求、风险边界和成功标准收敛为结构化 Objective 文档，确保后续 Spec/Test 能直接消费且无语义缺口。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 新需求立项 | 已收集上下文与干系人 | 可审查 Objective 草案 | 成功标准不可测 |
| 需求变更回合 | 变更影响范围已确认 | 更新后的目标边界与非目标 | 非目标缺失 |
| 评审前复核 | 目标草案已存在 | 可追溯的 scope baseline | 与 SSOT 冲突 |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-meta-asset-quality-hardening
input_contract:
  format: json
  required:
    - objective_context
    - stakeholders
    - constraints
    - success_criteria
  validation:
    - objective_context must explain current gap and target outcome
    - stakeholders must include decision owner
    - constraints must include explicit non-goals
    - success_criteria must be measurable and observable
output_contract:
  format: markdown
  required:
    - objective_ref
    - objective_statement
    - success_criteria
    - scope_baseline
    - non_goals
  machine_judgement:
    - all required sections are present
    - success criteria are testable
    - scope_baseline is traceable to input constraints
fail_closed_rules:
  - measurable success criteria missing
  - scope baseline or non-goals missing
  - objective violates architecture/process SSOT
test_mount:
  test_doc: skills/meta/objective-writer/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `objective_context` | string | 必须描述现状痛点与目标态 | 仅有口号、无具体问题 |
| `stakeholders` | array | 至少含 owner 与受影响角色 | 缺 owner |
| `constraints` | object | 必须包含边界与非目标 | 缺少 `non_goals` |
| `success_criteria` | array | 每条可验证、可观测 | 存在不可测条目 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `objective_ref` | string | 全局唯一且可追溯 | 规则匹配 + 去重检查 |
| `objective_statement` | string | 描述目标，不含实现细节 | 人审 + 规则匹配 |
| `scope_baseline` | object | 明确 in-scope/out-of-scope | 结构化字段校验 |
| `non_goals` | array | 与 `constraints` 一致 | 交叉一致性检查 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| 成功标准不可测 | `unverifiable_criteria > 0` | 拒绝输出并返回问题条目 | `2` |
| 范围边界缺失 | `scope_baseline` 缺字段 | 拒绝推进 | `2` |
| 与 SSOT 冲突 | `ssot_conflict=true` | 拒绝并要求重写 | `2` |
| 渲染/运行异常 | 运行期错误 | 记录异常并中止 | `1` |

## 运行命令

```bash
# objective-writer 为文档化技能，无独立 runner。
# 建议在产出后执行以下门禁：
python3 shared/registry/registry_contract_tool.py verify
```

## References

1. `skills/meta/objective-writer/references/objective-patterns.md`
2. `skills/meta/objective-writer/references/fail-closed-boundaries.md`
