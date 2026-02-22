---
name: "trigger-event-runtime"
description: "Runtime process for canonical event trigger orchestration"
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

# trigger-event-runtime

## Objective

将生命周期与业务事件触发转化为可审计运行实例，确保去重、补证据和升级链可执行。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: bpm, hr, admin
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: event_id, event_time, entity_type, entity_id, from_status, to_status, evidence_ref, match_policy_ref, dedupe_policy_ref, catchup_policy_ref

## Output Contract

- Format: json
- Required fields: trigger_receipt_ref, dedupe_decision, runtime_trace_ref

## Runtime Rules

1. 事件必须先归一再匹配，禁止直接执行目标流程。
2. 缺失证据引用默认 Fail-Closed，并发起补数请求。
3. 重复事件必须被显式拒绝并记录去重证据。
4. `catchup_policy_ref` 推荐编写规则见 `docs/design/processes/trigger-runtime-policy-guidelines.md`。

## Runtime Entrypoint

1. 可执行入口：`processes/control/trigger-event-runtime/scripts/trigger_event_runtime_runner.py`
2. 最小命令：
   - `python3 processes/control/trigger-event-runtime/scripts/trigger_event_runtime_runner.py --input <input.json> --output <output.json> --evidence-dir <evidence_dir>`
