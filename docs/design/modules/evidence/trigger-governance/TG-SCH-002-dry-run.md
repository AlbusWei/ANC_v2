# TG-SCH-002 Dry-Run Evidence

## Metadata

- Date: 2026-02-21
- Reviewer: Codex
- Branch: `codex/review-layers-modules`
- Mode: doc-level dry-run

## Input Snapshot

- Trigger definition:
  - `trigger_type=schedule`
  - `schedule=*/3 * * * *`
  - `delivery_policy=exception-only`
- Window condition:
  - 3 分钟窗口内无异常事件
- Preconditions:
  - trigger 已进入可执行范围（设计提案语义）
  - BPM 具备 trigger ledger 写入能力（文档约束）

## Expected Behaviour

1. 不推送 human/admin 消息。
2. 仅记录心跳执行账本。
3. 保留可审计 trigger receipt。

## Simulated Steps

1. 按提案构造一次 schedule tick（无异常输入）。
2. 走 `schedule trigger -> bpm` 链路。
3. 断言输出为 ledger heartbeat 记录，不创建异常推送动作。

## Evidence Refs

- trigger_ref: `dryrun://trigger/TG-SCH-002/tick-20260221T101500Z`
- ledger_ref: `dryrun://ledger/TG-SCH-002/heartbeat-20260221T101500Z`
- receipt_ref: `dryrun://receipt/TG-SCH-002/no-notify`

## Verdict

- Result: PASS
- Notes: 符合“无异常仅记账”策略，满足 `delivery_policy=exception-only` 设计约束。
