---
name: "quality-gate-preparation"
description: "Prepare executable quality gate bundle before implementation"
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

# quality-gate-preparation

## Objective

在实现前完成测试设计、datapoint 编译与 profile 绑定，形成可执行 preparation bundle。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: architect, bpm, qa, kernel-dev
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: objective_ref, spec_ref, test_doc_ref, risk_focus

## Output Contract

- Format: json
- Required fields: preparation_bundle_ref, preparation_evidence_ref, verdict

## Runtime Rules

1. 必须先于 `AP-006 implementation-execution` 执行完成。
2. 必须覆盖 P0 风险用例，缺失即 fail。
3. `tc_id -> profile_id` 映射缺失时 fail-closed。
