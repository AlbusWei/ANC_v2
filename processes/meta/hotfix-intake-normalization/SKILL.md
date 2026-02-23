---
name: "hotfix-intake-normalization"
description: "P5 子流程：按 hotfix profile 执行 AP-001/AP-002 归一化"
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

# hotfix-intake-normalization

## Objective

用于 hotfix 主流程入口，把 incident 上下文归一为可执行目标、影响范围与回滚方向。

## Input Contract

- Format: json
- Required fields: incident_context_ref

## Output Contract

- Format: json
- Required fields: hotfix_objective_ref, impact_scope_ref, rollback_direction_ref
