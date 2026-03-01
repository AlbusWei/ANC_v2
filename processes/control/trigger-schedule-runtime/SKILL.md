---
name: "trigger-schedule-runtime"
description: "Runtime process for schedule and heartbeat trigger orchestration"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.3.0"
---

# trigger-schedule-runtime

## Objective

将定时/心跳触发转化为可审计的流程实例调度，覆盖去重、补跑与升级闭环。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: bpm, admin
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: trigger_type, trigger_source, payload_ref, match_policy_ref, dedupe_policy_ref, catchup_policy_ref

## Output Contract

- Format: json
- Required fields: trigger_receipt_ref, runtime_trace_ref, catchup_decision

## Runtime Rules

1. schedule/heartbeat 输入必须先归一，再匹配去重。
2. 去重冲突不可判定时默认失败并升级。
3. 动态补跑窗口不可计算或超窗时必须输出升级记录。
4. `catchup_policy_ref` 推荐编写规则见 `docs/design/processes/trigger-runtime-policy-guidelines.md`。

## Runtime Entrypoint

1. 可执行入口：`processes/control/trigger-schedule-runtime/scripts/trigger_schedule_runtime_runner.py`
2. 最小命令：
   - `python3 processes/control/trigger-schedule-runtime/scripts/trigger_schedule_runtime_runner.py --input <input.json> --output <output.json> --evidence-dir <evidence_dir>`
