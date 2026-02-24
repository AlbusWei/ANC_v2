# trigger-event-runtime - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.2.0`
- Objective 引用：`obj-m2-trigger-governance-runtime`

## 流程目标（自然语言）

该流程是 M2 触发运行时对 lifecycle/event 触发的治理链，负责事件归一、匹配去重、实例分发与证据闭环，并在缺证据时触发补数或升级。它承担的是“事件到流程实例”的可靠桥接能力，确保状态变化不会因触发链不稳而失真。

## 协作编排原则

1. 该流程承担“事件到实例”的可靠桥接，不直接处理下游业务语义。
2. 事件归一与去重判定必须先于实例分发，避免重复或脏事件污染运行态。
3. 事件命中后的分发与证据记录必须原子化留痕，确保后续可审计可回放。
4. 证据缺口必须触发补数或升级，不允许以默认放行掩盖运行风险。
5. 异常路径收口必须明确责任归属，保证事件治理链可终止。

## 阶段语义定义

### p1 normalize-event-ingress

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：将事件归一为标准触发包。
- 输入语义：本阶段主要消费以下输入：event payload。
- 完成标准：完成判据：必须产出 canonical_trigger_ref，并满足“事件字段满足最小标准契约”。
- 交接说明：交接要求：将 canonical_trigger_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:trigger-event-runtime:p1`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.trigger-ingress-normalizer`，穿透执行策略：允许（同 Actor 场景）。

### p2 match-and-dedupe

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：匹配目标流程并完成事件去重。
- 输入语义：本阶段主要消费以下输入：canonical_trigger_ref。
- 完成标准：完成判据：必须产出 dedupe_decision，并满足“去重决策具备确定性且可追溯”。
- 交接说明：交接要求：将 dedupe_decision 交接给 p3。
- 执行单元：`subprocess:inline-ap:trigger-event-runtime:p2`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.trigger-matcher-dedupe`，穿透执行策略：允许（同 Actor 场景）。

### p3 dispatch-instance

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：为命中事件创建运行时实例。
- 输入语义：本阶段主要消费以下输入：dedupe_decision。
- 完成标准：完成判据：必须产出 instance_id，并满足“事件命中后仅产生一个实例”。
- 交接说明：交接要求：将 instance_id 交接给 p4。
- 执行单元：`subprocess:inline-ap:trigger-event-runtime:p3`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.process-instance-manager`，穿透执行策略：允许（同 Actor 场景）。

### p4 record-trigger-evidence

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：持久化触发回执与可追溯链路。
- 输入语义：本阶段主要消费以下输入：instance_id。
- 完成标准：完成判据：必须产出 trigger_receipt_ref，并满足“触发回执包含去重与分发决策”。
- 交接说明：交接要求：将 trigger_receipt_ref 交接给 p5。
- 执行单元：`subprocess:inline-ap:trigger-event-runtime:p4`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.evidence-recorder`，穿透执行策略：允许（同 Actor 场景）。

### p5 request-backfill-or-catchup

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：证据不足时给出补数或动态补跑决策。
- 输入语义：本阶段主要消费以下输入：trigger_receipt_ref。
- 完成标准：完成判据：必须产出 catchup_decision，并满足“证据缺失时会给出明确补数或升级提示”。
- 交接说明：交接要求：将 catchup_decision 交接给 p6。
- 执行单元：`subprocess:inline-ap:trigger-event-runtime:p5`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.catchup-scheduler`，穿透执行策略：允许（同 Actor 场景）。

### p6 escalate-runtime-anomaly

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：升级未解决的事件运行时异常。
- 输入语义：本阶段主要消费以下输入：catchup_decision。
- 完成标准：完成判据：必须产出 escalation_ref，并满足“升级链完整且可审计”。
- 交接说明：交接要求：将 escalation_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:trigger-event-runtime:p6`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.escalation-handler`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `p2`。
- `p2` 在 `success` 条件下流转到 `p3`（条件：dedupe_decision == allow）。
- `p2` 在 `success` 条件下流转到 `p4`（条件：dedupe_decision == reject）。
- `p3` 在 `success` 条件下流转到 `p4`。
- `p4` 在 `success` 条件下流转到 `p5`。
- `p5` 在 `success` 条件下流转到 `end`（条件：catchup_decision == run || catchup_decision == skip）。
- `p5` 在 `success` 条件下流转到 `p6`（条件：catchup_decision == escalate）。
- `p6` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
