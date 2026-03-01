---
name: "refactor"
description: "Refactor process for structural changes with mandatory regression and lifecycle sync"
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

# refactor

## Objective

在结构性重整任务中提供可治理流程，确保重构不会绕过测试、回归与生命周期审查。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: architect, kernel-dev, qa
- Priority support: P1 / P2

## Input Contract

- Format: json
- Required fields: objective_ref, scope_baseline_ref, tech_debt_ref, target_asset_ref

## Output Contract

- Format: json
- Required fields: refactor_delivery_bundle_ref, final_gate_verdict_ref, lifecycle_transition_ref, registry_sync_ref

## Runtime Rules

1. refactor 必须执行回归验证。
2. gate 未通过时禁止 lifecycle 迁移。
3. registry 证据缺失时禁止关闭任务。
