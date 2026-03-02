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
version: "0.3.1"
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
- Required fields: preparation_bundle_ref, actual_output_refs, superpower_ref
- Optional fields: profile_set（可覆盖默认 profile），max_auto_retest_cycles（默认 0，>0 时启用自动回测回路）

## Output Contract

- Format: json
- Required fields: gate_decision, runtime_gate_state, evidence_ref, final_gate_verdict_ref

## Runtime Rules

1. AP-008 主观评测默认启用。
2. 任一 P0 fail 必须阻断。
3. 出现 `runtime_gate_state=hold` 必须路由到 `hold-governance`。
4. 对外 `gate_decision` 枚举固定为 `pass|fail|test_invalid`，`hold` 只允许出现在 `runtime_gate_state`。
5. 当 `hold-governance` 返回 `retest_recommendation=auto-retest` 且预算未耗尽时，自动回路重跑评测链路。
