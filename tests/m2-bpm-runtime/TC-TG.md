# M2 BPM Runtime Trigger Governance Cases (W3)

## Scope

运行级验证 `trigger-schedule-runtime` 与 `trigger-event-runtime` 链路在 W3-A 的执行化闭环。

## Required Pass Set

- `TG-SCH-001`
- `TG-SCH-002`
- `TG-SCH-003`
- `TG-SCH-004`
- `TG-EVT-001`
- `TG-EVT-002`
- `TG-EVT-003`

## Case Definitions

### TG-SCH-001

- Input: schedule 窗口存在异常，`delivery_policy=exception-only`
- Expected:
  - 创建运行实例
  - 生成 `admin_forward_ref`
  - 输出 `trigger_receipt_ref` 与 `runtime_trace_ref`

### TG-SCH-002

- Input: schedule 窗口无异常
- Expected:
  - 不推送 admin/human
  - 生成 `trigger_ledger_ref`（heartbeat）
  - 证据链可追溯

### TG-SCH-003

- Input: owner override 当次任务
- Expected:
  - 不创建真实实例（保留虚拟 instance 占位）
  - 生成 `override_decision_ref` 与 `override_reason_ref`

### TG-SCH-004

- Input: 发生漏跑且在动态窗口内
- Expected:
  - `catchup_decision=run`
  - 生成 `catchup_run_ref`

### TG-EVT-001

- Input: lifecycle `review -> active` 事件
- Expected:
  - 规则命中并创建实例
  - 输出 `event_ref` 与 `trigger_receipt_ref`

### TG-EVT-002

- Input: 同一事件重复投递
- Expected:
  - `dedupe_decision=reject`
  - 生成 `dedupe_key_ref` 与 `dedupe_reject_log_ref`

### TG-EVT-003

- Input: 缺失 `transition_evidence_ref`
- Expected:
  - Fail-Closed（runner 返回码 2）
  - 生成 `fail_closed_record_ref` 与 `backfill_request_ref`

## Session Isolation Gate

1. 所有真实实例（`instance_id` 非 `virtual-*`）必须具备唯一 `session_id`。
2. 任意 `session_id` 若映射到多个 `instance_id`，判定跨实例污染并整体 FAIL。

## Suggested Command

```bash
python3 tests/m2-bpm-runtime/run_tc_tg.py
```
