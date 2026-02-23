---
name: "agent-creator"
description: "创建或更新 Agent 设计资产，并输出可直接进入 registry 审查的补丁计划"
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

# agent-creator

## Objective

在 Agent 资产创建/重构回合中，产出可审计、可追溯、可落盘的设计文档与 registry patch 计划，并对输入不完整场景执行 Fail-Closed。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 新增 Agent 角色 | `agent_id/role_scope/interfaces/owner` 完整 | 新 Agent 文档与工具文档路径 + registry patch 计划 | owner 缺失或接口协议不可解析 |
| 重构 Agent 边界 | 变更说明包含职责/边界差异 | 更新后的角色职责分层与依赖说明 | 边界与上层 SSOT 冲突 |
| 生命周期推进前审查 | 已有草案资产可读取 | 可进入 review 的补丁计划 | 核心字段缺失或证据链断裂 |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-meta-asset-quality-hardening
input_contract:
  format: json
  required:
    - agent_id
    - role_scope
    - interfaces
    - owner
  validation:
    - agent_id must be kebab-case and semantically stable
    - role_scope must contain responsibilities and boundaries
    - interfaces must include protocol_ref entries
    - owner must match an existing agent_id
output_contract:
  format: json
  required:
    - agent_doc_path
    - tools_doc_path
    - registry_patch_plan
  machine_judgement:
    - output json is parseable
    - paths are repo-relative and reachable
    - registry_patch_plan contains required lifecycle fields
fail_closed_rules:
  - missing mandatory input fields
  - invalid or unresolved protocol references
  - owner or lifecycle metadata mismatch
test_mount:
  test_doc: skills/meta/agent-creator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `agent_id` | string | kebab-case；语义稳定 | 空值、非法字符、模块编号命名 |
| `role_scope` | object | 必须同时含 `responsibilities` 与 `boundaries` | 任一子字段缺失 |
| `interfaces` | array | 至少 1 项，且每项含 `protocol_ref` | 空数组或 `protocol_ref` 缺失 |
| `owner` | string | 必须映射到现有 agent owner | 无法映射 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `agent_doc_path` | string | 指向角色设计文档 | 路径存在且可读 |
| `tools_doc_path` | string | 指向工具清单文档 | 路径存在且可读 |
| `registry_patch_plan` | object | 至少含 `skill_id/status/version/tests` | 结构化字段校验 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| 缺失必要输入 | `missing_fields != []` | 立即中止并返回缺失字段 | `2` |
| 协议引用无效 | `invalid_protocol_refs != []` | 中止并要求补齐协议引用 | `2` |
| 输出路径不可达 | 路径检查失败 | 中止并拒绝推进生命周期 | `2` |
| 运行时异常 | 未捕获异常 | 输出异常摘要，保留现场 | `1` |

## 运行命令

```bash
python3 skills/meta/agent-creator/scripts/agent_creator_runner.py \
  --input <input.json> \
  --output <output.json> \
  --report <report.json>
```

返回码约定：`0=success`，`2=fail-closed`，`1=unexpected error`。

## References

1. `skills/meta/agent-creator/references/input-output-schema.md`
2. `skills/meta/agent-creator/references/fail-closed-matrix.md`
