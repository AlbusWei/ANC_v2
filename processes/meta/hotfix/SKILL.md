---
name: "hotfix"
description: "Emergency fix process with fail-closed quality and lifecycle gate"
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

# hotfix

## Objective

在紧急修复场景下保持最小可治理闭环，确保快速修复不绕过质量门禁与生命周期审批。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: admin, bpm, kernel-dev
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: incident_ref, objective_ref, impact_scope, rollback_plan, target_asset_ref

## Output Contract

- Format: json
- Required fields: hotfix_delivery_bundle_ref, final_gate_verdict_ref, lifecycle_transition_ref, hotfix_release_package_ref

## Runtime Rules

1. 无回滚计划时禁止进入实现阶段。
2. hotfix gate 失败时必须阻断 release。
3. 任一阶段缺证据时 Fail-Closed。
