---
name: "registry-sync"
description: "AP-011 registry sync wrapper with fail-closed verification and auditable evidence"
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

# registry-sync

## Objective

执行 AP-011 注册表同步包装语义，保障 lifecycle 迁移后的 registry 同步与校验具备可审计证据链。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: hr, bpm, admin
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: target_registry_ref, registry_patch_plan_ref, requested_transition_ref, verify_scope, evidence_ref

## Output Contract

- Format: json
- Required fields: registry_sync_ref, registry_verify_report_ref, sync_decision, reasons

## Runtime Rules

1. 仅允许受控 registry 目标（skill/process/agent）。
2. 必须执行 `python3 shared/registry/registry_contract_tool.py verify`。
3. patch plan 缺失、路径冲突或 verify 失败时 Fail-Closed。

## Runtime Tooling

1. 可执行入口：`processes/meta/registry-sync/scripts/registry_sync_runner.py`
2. 最小命令：
   - `python3 processes/meta/registry-sync/scripts/registry_sync_runner.py --input <input.json> --output <output.json>`
