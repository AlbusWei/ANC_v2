---
name: "quality-gate-evaluation"
description: "Evaluate implementation outputs and aggregate gate decision"
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

# quality-gate-evaluation

## Objective

在实现后执行客观、主观、回归评测并输出统一 gate verdict。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: bpm, qa, architect
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: preparation_bundle_ref, actual_output_refs, profile_set

## Output Contract

- Format: json
- Required fields: gate_decision, runtime_gate_state, evidence_ref, final_gate_verdict_ref

## Runtime Rules

1. AP-008 主观评测默认启用。
2. 任一 P0 fail 必须阻断。
3. 出现 `runtime_gate_state=hold` 必须路由到 `hold-governance`。
4. 对外 `gate_decision` 枚举固定为 `pass|fail|test_invalid`，`hold` 只允许出现在 `runtime_gate_state`。
