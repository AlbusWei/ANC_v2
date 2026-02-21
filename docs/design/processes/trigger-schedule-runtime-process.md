# Trigger Schedule Runtime Process

> 版本: v0.2.0 | 层级: P4 | 类型: 复合流程 | process_id: trigger-schedule-runtime

## 目标

处理 `schedule|heartbeat` 类触发，完成归一、匹配去重、实例调度、证据归档、补跑与升级闭环。

## 连续性边界

1. 本流程只覆盖触发运行时生命周期段，不跨越资产生命周期审批段。
2. 目标流程执行属于下游流程实例范围，本流程只负责触发侧编排与留痕。
3. 补跑决策与升级决策保持在同一连续运行治理段内。

## 阶段定义

1. `normalize-trigger-ingress`（AP-026）
2. `match-and-dedupe`（AP-027）
3. `dispatch-instance`（AP-028）
4. `record-trigger-evidence`（AP-029）
5. `schedule-catchup`（AP-030）
6. `escalate-runtime-anomaly`（AP-031）

## 阶段到原子流程映射

| 阶段 | 原子流程 | 输出 |
|---|---|---|
| normalize-trigger-ingress | AP-026 | canonical_trigger_ref |
| match-and-dedupe | AP-027 | match_result + dedupe_decision |
| dispatch-instance | AP-028 | instance_id + dispatch_receipt_ref |
| record-trigger-evidence | AP-029 | trigger_receipt_ref + evidence_index_ref |
| schedule-catchup | AP-030 | catchup_decision + catchup_run_ref |
| escalate-runtime-anomaly | AP-031 | escalation_ref + escalation_trace |

## 输入契约

1. `trigger_type`
2. `trigger_source`
3. `payload_ref`
4. `match_policy_ref`
5. `dedupe_policy_ref`
6. `catchup_policy_ref`

`catchup_policy_ref` 编写基线：`docs/design/processes/trigger-runtime-policy-guidelines.md`。

## 输出契约

1. `trigger_receipt_ref`
2. `instance_id`（可选，未命中时为空）
3. `catchup_decision`
4. `escalation_ref`（可选）
5. `runtime_trace_ref`

## 去重策略

1. 主键：`source + event_id`
2. 回退键：`source + canonical_event + entity_type + entity_id + from_status + to_status + emitted_by + time_bucket`
3. 主键与回退键均不可构造或冲突不可判定时，Fail-Closed 并升级。

## Fail-Closed 规则

1. 去重冲突不可判定 -> `fail` 并升级。
2. 关键输入缺失或证据不可达 -> `fail`。
3. 触发命中后实例创建失败 -> `fail`。
4. 动态补跑窗口不可计算或超窗且无法升级 -> `fail`。

## 依赖流程

1. `docs/design/processes/atomic/AP-026-trigger-ingress-normalization.md`
2. `docs/design/processes/atomic/AP-027-trigger-match-and-dedupe.md`
3. `docs/design/processes/atomic/AP-028-trigger-dispatch-and-instance-start.md`
4. `docs/design/processes/atomic/AP-029-trigger-evidence-recording.md`
5. `docs/design/processes/atomic/AP-030-trigger-catchup-scheduling.md`
6. `docs/design/processes/atomic/AP-031-trigger-escalation-handling.md`
