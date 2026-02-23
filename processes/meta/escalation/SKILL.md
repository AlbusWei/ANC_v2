---
name: "escalation"
description: "P5 reusable escalation subprocess with fixed governance chain and fail-closed routing"
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

# escalation

## Objective

执行统一升级治理子流程，在异常、冲突或权限不足场景中按固定升级链输出可审计决策。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: bpm, qa, admin, architect
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: incident_ref, severity, current_owner, escalation_policy_ref, evidence_ref

## Output Contract

- Format: json
- Required fields: escalation_ref, escalation_trace, final_owner, escalation_decision, reasons

## Runtime Rules

1. 升级链固定 `actor -> owner -> bpm -> admin -> human`，禁止越级。
2. `severity` 仅允许 `low|medium|high|critical`。
3. `critical` 场景必须可达 `admin` 或 `human`，否则 Fail-Closed。

## Runtime Tooling

1. 可执行入口：`processes/meta/escalation/scripts/escalation_runner.py`
2. 最小命令：
   - `python3 processes/meta/escalation/scripts/escalation_runner.py --input <input.json> --output <output.json>`
