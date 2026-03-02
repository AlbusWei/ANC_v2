---
name: "development-process"
description: "Meta minimum development loop for Objective->Spec->Test->Implement->Gate->Lifecycle"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.5.1"
---

# development-process

## Objective

提供 ANC v2 可复用的最小开发闭环内核，让上层业务流程在不引入发布与演化开销前提下，先完成可验证实现并闭合最小生命周期治理。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: admin, architect, bpm
- Priority support: P0 / P1 / P2

## Input Contract

- Format: json
- Required fields: objective_context_ref, target_asset_ref, requested_transition, superpower_ref

## Output Contract

- Format: json
- Required fields: objective_ref, scope_baseline_ref, spec_ref, test_plan_ref, implementation_ref, final_gate_verdict_ref, lifecycle_transition_ref, registry_sync_ref

## Runtime Rules

1. 必须经 BPM 分发，禁止绕过 phase 编排直接执行单技能。
2. 默认使用 phase 级 isolated session，跨 phase 不复用同一会话。
3. `p5` 门禁失败时仅允许回流 `p4`，并受 `max_iterations=2` 约束；`p5` 仅在 `gate_decision == pass` 时进入 `p6`。
4. `p6` 必须完成 `lifecycle_transition_ref` 与 `registry_sync_ref` 双证据收口。
5. 任一阶段输入/输出语义断裂时 Fail-Closed。
