---
name: "implementation-execution-core"
description: "P5 子流程：AP-006 实施执行核心"
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

# implementation-execution-core

## Objective

统一实现执行阶段的输入/输出契约，确保 `spec_ref + test_plan_ref -> implementation_ref` 可复用。

## Input Contract

- Format: json
- Required fields: spec_ref, test_plan_ref

## Output Contract

- Format: json
- Required fields: implementation_ref
