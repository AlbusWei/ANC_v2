---
name: "process-template"
description: "Template blueprint for canonical BPM process assets"
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

# process-template

用于初始化 Process 资产（`SKILL.md` + `PROCESS.md` + `process.json`），并默认对齐当前 BPM canonical schema。

## Objective

提供可直接复用的流程蓝图，确保新流程从创建阶段就符合 `subprocess + control_flow + fail_policy + inline_ap` 标准。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: bpm, architect
- Priority support: P0 / P1 / P2

## Input Contract

- Format: json
- Required fields: objective_context_ref

## Output Contract

- Format: json
- Required fields: phase_outputs_ref, final_verdict_ref

## Runtime Rules

1. phase 必须使用 `target_type=subprocess`。
2. 未注册子流程必须通过 `inline_ap` 声明 skill 映射。
3. 控制流必须显式声明成功、失败回路与终止态。
4. 任一阶段输入/输出不可追溯时 Fail-Closed。
