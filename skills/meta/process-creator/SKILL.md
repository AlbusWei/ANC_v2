---
name: "process-creator"
description: "创建或重构流程资产，强制满足连续性约束、phase 闭合约束与断点拆分规则"
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

# process-creator

## Objective

输出符合流程标准的 `PROCESS.md/SKILL.md/process.json` 资产，并在生成阶段即阻断连续性违规或 phase 不闭合的流程定义。

## 触发矩阵

| 触发条件 | 输入前置 | 输出目标 | 阻断条件 |
|---|---|---|---|
| 新增复合流程 | 生命周期段与 phase 草案完整 | 通过校验的流程三件套 | 跨非连续生命周期段 |
| 重构既有流程 | 已有流程清单与变更目标 | 更新后的闭合 phase 映射 | phase 无目标映射 |
| 发布前门禁 | process.json 已生成 | 可进入 registry 的 patch 计划 | `requires_spec=true` 但缺 `spec_ref` |

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-meta-asset-quality-hardening
input_contract:
  format: json
  required:
    - process_id
    - process_level
    - phases
    - control_flow
    - fail_policy
  validation:
    - process_id must be kebab-case
    - phases must be non-empty and phase-closed
    - control_flow must be bounded with explicit terminal states
    - fail_policy must define rollback route
output_contract:
  format: json
  required:
    - process_manifest_path
    - process_skill_path
    - process_guide_path
  machine_judgement:
    - process.json includes required canonical fields
    - every phase has target_type and target_id
    - spec_ref exists when requires_spec is true
fail_closed_rules:
  - lifecycle continuity violation
  - phase closure violation
  - unresolved breakpoint crossing without parent orchestration
test_mount:
  test_doc: skills/meta/process-creator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## 输入字段约束

| 字段 | 类型 | 约束 | Fail-Closed 条件 |
|---|---|---|---|
| `process_id` | string | kebab-case 且语义稳定 | 非法命名 |
| `process_level` | string | 必须属于定义层级集合 | 非法层级 |
| `phases` | array | 每 phase 必须有 `phase_id/target_type/target_id` | 任一 phase 缺字段 |
| `control_flow` | object | 必须包含终止与异常路径 | 无终止态 |
| `fail_policy` | object | 必须包含回滚策略 | 缺失回滚路径 |

## 输出字段约束

| 字段 | 类型 | 约束 | 验证方式 |
|---|---|---|---|
| `process_manifest_path` | string | 指向 `process.json` | JSON schema 校验 |
| `process_skill_path` | string | 指向流程级 `SKILL.md` | 文件存在性检查 |
| `process_guide_path` | string | 指向流程说明文档 | 文件存在性检查 |

## Fail-Closed 决策表

| 场景 | 检测信号 | 决策 | 返回码 |
|---|---|---|---|
| 连续性违规 | `continuity_violation=true` | 阻断并返回违规 phase | `2` |
| phase 不闭合 | `phase_closure_violation=true` | 阻断并输出缺失映射 | `2` |
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
