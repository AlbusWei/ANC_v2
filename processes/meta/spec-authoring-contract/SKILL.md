---
name: "spec-authoring-contract"
description: "P5 子流程：AP-004 规格产出契约"
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

# spec-authoring-contract

## Objective

统一规格产出语义，作为唯一 `spec_ref` 产出子流程供多个主流程复用。

## Input Contract

- Format: json
- Required fields: objective_ref, scope_baseline_ref

## Output Contract

- Format: json
- Required fields: spec_ref
