---
name: "objective-scope-baseline"
description: "P5 子流程：按 AP-001/AP-002/AP-003 生成 objective 与 scope baseline"
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

# objective-scope-baseline

## Objective

将目标语义收敛与范围基线固化为可复用 P5 子流程，为 full-development/refactor 提供一致输入。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: architect, bpm
- Priority support: P1

## Input Contract

- Format: json
- Required fields: objective_context_ref

## Output Contract

- Format: json
- Required fields: objective_ref, scope_baseline_ref
