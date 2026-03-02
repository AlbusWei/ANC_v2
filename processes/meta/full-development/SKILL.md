---
name: "full-development"
description: "Full reflexive development loop for internal assets with quality gate and lifecycle handoff"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.3.1"
---

# full-development

## Objective

执行系统资产的全链路开发流程，确保 Objective/Spec/Test/Implement/Verify/Lifecycle 在一条可审计链路中闭环。

## Invocation

- Entry manifest: `process.json`
- Runtime runner: `scripts/full_development_runner.py`
- Initiator roles: architect, qa, kernel-dev, admin
- Priority support: P0 / P1 / P2

## Input Contract

- Format: json
- Required fields: objective_context_ref, input_payload, target_asset_type, lifecycle_target, superpower_ref

## Output Contract

- Format: json
- Required fields: m3_delivery_bundle_ref, final_gate_verdict_ref, lifecycle_transition_ref

## Runtime Rules

1. `quality-gate-evaluation` 未通过时禁止进入 lifecycle/release。
2. 任一阶段缺证据时默认 Fail-Closed。
3. `release_required=true` 时必须生成 release 证据。
4. 协作模式默认要求真实 OpenClaw 分发（`--dispatch-openclaw`）。
5. phase 级会话默认每阶段 reset（`--reset-openclaw-session`），避免同 actor 会话上下文堆积。
