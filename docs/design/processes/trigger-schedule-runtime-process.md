# Trigger Schedule Runtime Process

> 版本: v0.3.0 | 层级: P4 | 类型: 复合流程 | process_id: trigger-schedule-runtime

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

## 运行入口（W3-A）

1. 可执行 runner：`processes/control/trigger-schedule-runtime/scripts/trigger_schedule_runtime_runner.py`
2. 核心阶段 runner 绑定：
   - `sys.bpm.trigger-ingress-normalizer` -> `skills/system/trigger-ingress-normalizer/scripts/trigger_ingress_normalizer_runner.py`
   - `sys.bpm.trigger-matcher-dedupe` -> `skills/system/trigger-matcher-dedupe/scripts/trigger_matcher_dedupe_runner.py`
   - `sys.bpm.evidence-recorder` -> `skills/system/evidence-recorder/scripts/evidence_recorder_runner.py`
   - `sys.bpm.catchup-scheduler` -> `skills/system/catchup-scheduler/scripts/catchup_scheduler_runner.py`
   - `sys.bpm.escalation-handler` -> `skills/system/escalation-handler/scripts/escalation_handler_runner.py`
3. 回归入口：`tests/m2-bpm-runtime/run_tc_tg.py`（覆盖 `TG-SCH-001~004`）。

## 协作策略（M3 对齐）

1. 流程 manifest 启用 `collaboration_policy`：`mode=phase-isolated-session`。
2. 分发运行时固定 `dispatch_runtime=openclaw-required`。
3. 同 actor 跨 phase 采用 `session_reset=per-phase-reset`，避免会话上下文污染。

## 去重策略

1. 主键：`source + event_id`
2. 回退键：`source + canonical_event + entity_type + entity_id + from_status + to_status + emitted_by + time_bucket`
3. 主键与回退键均不可构造或冲突不可判定时，Fail-Closed 并升级。

## Fail-Closed 规则

1. 去重冲突不可判定 -> `fail` 并升级。
2. 关键输入缺失或证据不可达 -> `fail`。
3. 触发命中后实例创建失败 -> `fail`。
4. 动态补跑窗口不可计算或超窗且无法升级 -> `fail`。
5. 任意跨实例 `session_id` 复用 -> `fail` 并留证据（继承 W1 会话隔离门禁）。

## 运行证据落盘（W3-A）

1. 用例证据目录：`runtime_data/execution/evidence/bpm-runtime/w3_trigger_runtime_cases/TG-SCH-*`
2. 汇总报告：`runtime_data/execution/evidence/bpm-runtime/w3_tc_tg_report.json`
3. 执行总结：`runtime_data/execution/evidence/bpm-runtime/w3_execution_summary.md`

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
| `p1` | `bpm` | 归一化外部触发包。 | trigger payload | 产出 canonical_trigger_ref，并满足：标准触发包包含必需字段 | 将 canonical_trigger_ref 交接给 p2 |
| `p2` | `bpm` | 按匹配规则与去重策略做准入判定。 | canonical_trigger_ref | 产出 match_result，并满足：去重决策明确为 allow 或 reject | 将 match_result 交接给 p3 |
| `p3` | `bpm` | 匹配命中时创建流程运行实例。 | match_result | 产出 instance_id，并满足：命中触发具备 instance_id 与状态迁移记录 | 将 instance_id 交接给 p4 |
| `p4` | `bpm` | 持久化触发回执与可追溯链路。 | instance_id | 产出 trigger_receipt_ref，并满足：触发与实例可双向追溯 | 将 trigger_receipt_ref 交接给 p5 |
| `p5` | `bpm` | 评估动态补跑策略与漏跑处置。 | trigger_receipt_ref | 产出 catchup_decision，并满足：补跑决策具备确定性 | 将 catchup_decision 交接给 p6 |
| `p6` | `bpm` | 升级未解决的运行时异常。 | catchup_decision | 产出 escalation_ref，并满足：升级链遵循 actor-owner-bpm-admin-human | 将 escalation_ref 交接给 initiator |
<!-- phase-semantics-v2:end -->
