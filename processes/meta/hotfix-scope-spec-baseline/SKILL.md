---
name: "hotfix-scope-spec-baseline"
description: "P5 子流程：AP-003 + spec-authoring-contract 组合，生成 hotfix scope/spec 基线"
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

# hotfix-scope-spec-baseline

## Objective

通过组合 AP-003 与 `spec-authoring-contract`，在 hotfix 场景下解耦 AP-004 语义复用。

## Input Contract

- Format: json
- Required fields: hotfix_objective_ref, impact_scope_ref

## Output Contract

- Format: json
- Required fields: hotfix_scope_baseline_ref, hotfix_spec_ref
