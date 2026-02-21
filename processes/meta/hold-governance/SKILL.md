---
name: "hold-governance"
description: "Govern hold cases with triage, health maintenance and escalation"
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

# hold-governance

## Objective

将 hold 场景治理为可执行流程，统一 triage、恢复与升级闭环。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: qa, bpm
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: hold_case_ref, runtime_log_ref, execution_state_ref, triage_policy_ref, runtime_health_policy_ref

## Output Contract

- Format: json
- Required fields: triage_report_ref, health_maintenance_ref, hold_resolution_ref

## Runtime Rules

1. triage 决策只允许 `continue|retry|debug|fail`。
2. 禁止固定超时直接判 fail。
3. 升级链固定 `qa -> bpm -> admin`。
