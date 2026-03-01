---
name: "process-creator"
description: "创建或重构流程资产，强制满足 canonical schema、phase 闭合与 inline_ap 语义"
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

# process-creator

## Objective

输出符合当前流程标准的 `PROCESS.md/SKILL.md/process.json` 资产，并在生成阶段即阻断 schema 偏差、phase 不闭合、inline_ap 映射错误等问题。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 新增复合流程 | 生命周期段与 phase 草案完整 | 通过校验的流程三件套 | 跨非连续生命周期段 / phase 不闭合 |
| 重构既有流程 | 已有流程清单与变更目标 | 更新后的闭合 phase 映射 | legacy 字段或 target_type 非 subprocess |
| 发布前门禁 | process.json 已生成 | 可进入 registry 的 patch 计划 | `requires_spec=true` 且缺 `spec_ref` |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.1.0
objective_ref: obj-m3-meta-asset-quality-hardening
input_contract:
  format: json
  required:
    - process_id
    - version
    - process_level
    - phases
    - control_flow
    - fail_policy
    - evidence_policy
    - lineage_policy
  validation:
    - process_id must be kebab-case
    - process_level must be p1~p6
    - phases must be non-empty and phase-closed
    - target_type must be subprocess
    - P4 requires collaboration_policy(mode/dispatch_runtime/session_reset)
    - P5/P6 with multi-actor collaboration require collaboration_policy
    - requires_spec=true requires spec_ref (repo_relative_path#anchor)
    - unregistered target_id requires inline_ap binding to skill_registry
    - control_flow must include terminal end
output_contract:
  format: json
  required:
    - process_manifest_path
    - process_skill_path
    - process_guide_path
    - registry_patch_plan
  machine_judgement:
    - process.json includes canonical required fields
    - each phase contains semantic fields and executable target mapping
    - legacy fields (control/failure_policy/skill_or_process) are rejected
fail_closed_rules:
  - lifecycle continuity violation
  - phase closure violation
  - unresolved inline_ap mapping
  - invalid control_flow terminal or edge mapping
test_mount:
  test_doc: skills/meta/process-creator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `process_id` | string | kebab-case 且语义稳定 | 非法命名 |
| `version` | string | semver | 非法版本 |
| `process_level` | string | 必须属于 p1~p6 | 非法层级 |
| `phases` | array | 每 phase 必须有 canonical 字段 + 语义字段 | 任一 phase 缺字段 |
| `control_flow` | array | 必须包含终止态 `to=end` | 无终止态 |
| `fail_policy` | object | 必须包含 fail_closed + retry + escalation_chain | 缺失回退/升级策略 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `process_manifest_path` | string | 指向 `process.json` | JSON schema 校验 |
| `process_skill_path` | string | 指向流程级 `SKILL.md` | 文件存在性检查 |
| `process_guide_path` | string | 指向流程说明文档 | 文件存在性检查 |
| `registry_patch_plan` | object | 含 process_id/status/version | registry 入库前检查 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| legacy 字段违规 | `control/failure_policy` 出现 | 阻断并返回违规字段 | `2` |
| phase 不闭合 | phase 字段缺失或无法映射 | 阻断并输出缺失映射 | `2` |
| inline_ap 错误 | target 未注册且 inline_ap 不合法 | 阻断并输出映射错误 | `2` |
| spec 引用缺失 | `requires_spec=true` 且无 `spec_ref` | 阻断并返回缺失字段 | `2` |
| 运行时异常 | 未捕获异常 | 中止并记录异常 | `1` |

## 运行命令

```bash
python3 skills/meta/process-creator/scripts/process_creator_runner.py \
  --input <input.json> \
  --output <output.json> \
  --report <report.json>
```

返回码约定：`0=success`，`2=fail-closed`，`1=unexpected error`。

## References

1. `skills/meta/process-creator/references/process-manifest-schema.md`
2. `skills/meta/process-creator/references/phase-closure-checklist.md`
