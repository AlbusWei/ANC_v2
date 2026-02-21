---
name: "governed-config-change"
description: "Governed OpenClaw configuration change process with BPM gatekeeping and admin execution"
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

# governed-config-change

## Objective

为系统配置变更提供可执行治理流程，确保“请求-审批-执行-校验-归档”全链路可审计。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: personal-assistant, bpm, admin, architect, hr
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: objective_ref, change_request, requester, target_scope, rollback_plan

## Output Contract

- Format: json
- Required fields: final_output, evidence_refs, verdict, change_receipt

## Runtime Rules

1. 涉及系统级配置写操作时，执行者固定为 admin。
2. BPM 必须在执行前完成门禁校验（objective/spec/test + rollback_plan）。
3. 执行前后必须记录配置 hash 与验证结果。
4. 证据缺失、hash 漂移或验证失败时 Fail-Closed。
