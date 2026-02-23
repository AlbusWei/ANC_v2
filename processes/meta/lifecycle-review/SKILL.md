---
name: "lifecycle-review"
description: "Lifecycle governance approval flow with quality-gate prerequisite and registry sync verification"
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

# lifecycle-review

## Objective

为资产生命周期迁移提供最小可执行治理接点，保证 `M1 -> M4` 迁移请求在证据齐备、质量门禁通过、registry 校验通过后才可落盘。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: hr, bpm, architect
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: final_gate_verdict_ref, target_asset_ref, requested_transition

## Output Contract

- Format: json
- Required fields: lifecycle_transition_ref, registry_sync_ref, lifecycle_review_report_ref

## Runtime Rules

1. `requested_transition` 必须满足 5 态状态机的合法迁移。
2. `final_gate_verdict_ref` 未通过（非 `pass`）时直接 Fail-Closed。
3. registry 校验命令失败时直接 Fail-Closed。
4. owner 固定为 `hr`；`system-analyst` 仅作为分析输入提供方。

## Runtime Tooling

1. 可执行入口：`python3 processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py --input <input.json> --output <output.json>`
2. 默认 registry 校验命令：`python3 shared/registry/registry_contract_tool.py verify`
