# Trigger Event Runtime Process

> 版本: v0.2.0 | 层级: P4 | 类型: 复合流程 | process_id: trigger-event-runtime

## 目标

处理事件触发链路，保障 `review -> active` 等生命周期事件在 M2 运行时侧具备可执行、可去重、可补证据闭环。

## 连续性边界

1. 本流程覆盖事件触发运行段，不承担策略审批（由 M4 负责）。
2. 事件处理仅进入目标流程实例，不跨入目标流程业务实现阶段。
3. 缺证据事件必须在同流程内触发补数或升级，不允许静默放行。

## 阶段定义

1. `normalize-event-ingress`（AP-026）
2. `match-and-dedupe`（AP-027）
3. `dispatch-instance`（AP-028）
4. `record-trigger-evidence`（AP-029）
5. `request-backfill-or-catchup`（AP-030）
6. `escalate-runtime-anomaly`（AP-031）

## 阶段到原子流程映射

| 阶段 | 原子流程 | 输出 |
|---|---|---|
| normalize-event-ingress | AP-026 | canonical_trigger_ref |
| match-and-dedupe | AP-027 | match_result + dedupe_decision |
| dispatch-instance | AP-028 | instance_id + dispatch_receipt_ref |
| record-trigger-evidence | AP-029 | trigger_receipt_ref + traceability_link_ref |
| request-backfill-or-catchup | AP-030 | catchup_decision + escalation_hint |
| escalate-runtime-anomaly | AP-031 | escalation_ref + escalation_trace |

## 输入契约

1. `event_id`
2. `event_time`
3. `entity_type`
4. `entity_id`
5. `from_status`
6. `to_status`
7. `evidence_ref`
8. `match_policy_ref`
9. `dedupe_policy_ref`
10. `catchup_policy_ref`

`catchup_policy_ref` 编写基线：`docs/design/processes/trigger-runtime-policy-guidelines.md`。

## 输出契约

1. `trigger_receipt_ref`
2. `instance_id`（可选，未命中时为空）
3. `dedupe_decision`
4. `backfill_request_ref`（可选）
5. `escalation_ref`（可选）

## 去重策略

1. 主键：`source + event_id`
2. 回退键：`source + canonical_event + entity_type + entity_id + from_status + to_status + emitted_by + time_bucket`
3. 主键与回退键均不可构造或冲突不可判定时，Fail-Closed 并触发补数/升级。

## Fail-Closed 规则

1. 事件最小字段缺失 -> `fail` 并触发补数请求。
2. 去重冲突不可判定 -> `fail`。
3. 事件命中但证据链不可追溯 -> `fail`。
4. 升级链断裂或越级 -> `fail`。

## 依赖流程

1. `docs/design/processes/atomic/AP-026-trigger-ingress-normalization.md`
2. `docs/design/processes/atomic/AP-027-trigger-match-and-dedupe.md`
3. `docs/design/processes/atomic/AP-028-trigger-dispatch-and-instance-start.md`
4. `docs/design/processes/atomic/AP-029-trigger-evidence-recording.md`
5. `docs/design/processes/atomic/AP-030-trigger-catchup-scheduling.md`
6. `docs/design/processes/atomic/AP-031-trigger-escalation-handling.md`
