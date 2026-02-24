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

## 运行入口（W3-A）

1. 可执行 runner：`processes/control/trigger-event-runtime/scripts/trigger_event_runtime_runner.py`
2. 核心阶段 runner 绑定：
   - `sys.bpm.trigger-ingress-normalizer` -> `skills/system/trigger-ingress-normalizer/scripts/trigger_ingress_normalizer_runner.py`
   - `sys.bpm.trigger-matcher-dedupe` -> `skills/system/trigger-matcher-dedupe/scripts/trigger_matcher_dedupe_runner.py`
   - `sys.bpm.evidence-recorder` -> `skills/system/evidence-recorder/scripts/evidence_recorder_runner.py`
   - `sys.bpm.catchup-scheduler` -> `skills/system/catchup-scheduler/scripts/catchup_scheduler_runner.py`
   - `sys.bpm.escalation-handler` -> `skills/system/escalation-handler/scripts/escalation_handler_runner.py`
3. 回归入口：`tests/m2-bpm-runtime/run_tc_tg.py`（覆盖 `TG-EVT-001~003`）。

## 去重策略

1. 主键：`source + event_id`
2. 回退键：`source + canonical_event + entity_type + entity_id + from_status + to_status + emitted_by + time_bucket`
3. 主键与回退键均不可构造或冲突不可判定时，Fail-Closed 并触发补数/升级。

## Fail-Closed 规则

1. 事件最小字段缺失 -> `fail` 并触发补数请求。
2. 去重冲突不可判定 -> `fail`。
3. 事件命中但证据链不可追溯 -> `fail`。
4. 升级链断裂或越级 -> `fail`。
5. 任意跨实例 `session_id` 复用 -> `fail` 并留证据（继承 W1 会话隔离门禁）。

## 运行证据落盘（W3-A）

1. 用例证据目录：`docs/design/modules/evidence/bpm-runtime/w3_trigger_runtime_cases/TG-EVT-*`
2. 汇总报告：`docs/design/modules/evidence/bpm-runtime/w3_tc_tg_report.json`
3. 执行总结：`docs/design/modules/evidence/bpm-runtime/w3_execution_summary.md`

## 依赖流程

1. `docs/design/processes/atomic/AP-026-trigger-ingress-normalization.md`
2. `docs/design/processes/atomic/AP-027-trigger-match-and-dedupe.md`
3. `docs/design/processes/atomic/AP-028-trigger-dispatch-and-instance-start.md`
4. `docs/design/processes/atomic/AP-029-trigger-evidence-recording.md`
5. `docs/design/processes/atomic/AP-030-trigger-catchup-scheduling.md`
6. `docs/design/processes/atomic/AP-031-trigger-escalation-handling.md`

<!-- phase-semantics-v2:start -->
## 阶段协作语义补充（v2）

> 说明：本节用于说明每个 phase 在系统主线中的职责与协作价值，要求可直接回答“为什么由该 Actor 在该阶段执行该动作”。

| phase_id | Actor | 阶段目的 | 输入语义 | 完成标准 | 交接语义 |
|---|---|---|---|---|---|
| `p1` | `bpm` | 将事件归一为标准触发包。 | event payload | 产出 canonical_trigger_ref，并满足：事件字段满足最小标准契约 | 将 canonical_trigger_ref 交接给 p2 |
| `p2` | `bpm` | 匹配目标流程并完成事件去重。 | canonical_trigger_ref | 产出 dedupe_decision，并满足：去重决策具备确定性且可追溯 | 将 dedupe_decision 交接给 p3 |
| `p3` | `bpm` | 为命中事件创建运行时实例。 | dedupe_decision | 产出 instance_id，并满足：事件命中后仅产生一个实例 | 将 instance_id 交接给 p4 |
| `p4` | `bpm` | 持久化触发回执与可追溯链路。 | instance_id | 产出 trigger_receipt_ref，并满足：触发回执包含去重与分发决策 | 将 trigger_receipt_ref 交接给 p5 |
| `p5` | `bpm` | 证据不足时给出补数或动态补跑决策。 | trigger_receipt_ref | 产出 catchup_decision，并满足：证据缺失时会给出明确补数或升级提示 | 将 catchup_decision 交接给 p6 |
| `p6` | `bpm` | 升级未解决的事件运行时异常。 | catchup_decision | 产出 escalation_ref，并满足：升级链完整且可审计 | 将 escalation_ref 交接给 initiator |
<!-- phase-semantics-v2:end -->
