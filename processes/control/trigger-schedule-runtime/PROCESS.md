# trigger-schedule-runtime - 流程说明

## 流程定位

- 流程级别：`P4`
- 负责人：`bpm`
- 版本：`0.2.0`
- Objective 引用：`obj-m2-trigger-governance-runtime`

## 流程目标（自然语言）

该流程是 M2 触发运行时对 schedule/heartbeat 触发的治理链，负责把外部触发转成可执行实例，并同步完成去重、证据、补跑与异常升级。它在系统中的意义是保证“定时驱动”具备可追溯与可恢复能力，而非仅仅触发一次执行。

## 协作编排原则

1. 该流程只负责触发治理，不承载被触发业务流程的业务执行语义。
2. 去重与实例分发必须具备确定性：同一触发在同策略下不得产生歧义结果。
3. 触发证据、实例状态与回执必须可双向追溯，避免“触发了但不可证明”。
4. 补跑决策必须在流程内完成闭环，不能把漏跑问题静默转嫁到下游。
5. 无法恢复的异常必须沿升级链收口，禁止以忽略或重试风暴替代治理。

## 阶段语义定义

### p1 normalize-trigger-ingress

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：归一化外部触发包。
- 输入语义：本阶段主要消费以下输入：trigger payload。
- 完成标准：完成判据：必须产出 canonical_trigger_ref，并满足“标准触发包包含必需字段”。
- 交接说明：交接要求：将 canonical_trigger_ref 交接给 p2。
- 执行单元：`subprocess:inline-ap:trigger-schedule-runtime:p1`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.trigger-ingress-normalizer`，穿透执行策略：允许（同 Actor 场景）。

### p2 match-and-dedupe

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：按匹配规则与去重策略做准入判定。
- 输入语义：本阶段主要消费以下输入：canonical_trigger_ref。
- 完成标准：完成判据：必须产出 match_result，并满足“去重决策明确为 allow 或 reject”。
- 交接说明：交接要求：将 match_result 交接给 p3。
- 执行单元：`subprocess:inline-ap:trigger-schedule-runtime:p2`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.trigger-matcher-dedupe`，穿透执行策略：允许（同 Actor 场景）。

### p3 dispatch-instance

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：匹配命中时创建流程运行实例。
- 输入语义：本阶段主要消费以下输入：match_result。
- 完成标准：完成判据：必须产出 instance_id，并满足“命中触发具备 instance_id 与状态迁移记录”。
- 交接说明：交接要求：将 instance_id 交接给 p4。
- 执行单元：`subprocess:inline-ap:trigger-schedule-runtime:p3`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.process-instance-manager`，穿透执行策略：允许（同 Actor 场景）。

### p4 record-trigger-evidence

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：持久化触发回执与可追溯链路。
- 输入语义：本阶段主要消费以下输入：instance_id。
- 完成标准：完成判据：必须产出 trigger_receipt_ref，并满足“触发与实例可双向追溯”。
- 交接说明：交接要求：将 trigger_receipt_ref 交接给 p5。
- 执行单元：`subprocess:inline-ap:trigger-schedule-runtime:p4`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.evidence-recorder`，穿透执行策略：允许（同 Actor 场景）。

### p5 schedule-catchup

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：评估动态补跑策略与漏跑处置。
- 输入语义：本阶段主要消费以下输入：trigger_receipt_ref。
- 完成标准：完成判据：必须产出 catchup_decision，并满足“补跑决策具备确定性”。
- 交接说明：交接要求：将 catchup_decision 交接给 p6。
- 执行单元：`subprocess:inline-ap:trigger-schedule-runtime:p5`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.catchup-scheduler`，穿透执行策略：允许（同 Actor 场景）。

### p6 escalate-runtime-anomaly

- 执行角色：`bpm`
- 阶段目的：本阶段围绕以下业务动作推进：升级未解决的运行时异常。
- 输入语义：本阶段主要消费以下输入：catchup_decision。
- 完成标准：完成判据：必须产出 escalation_ref，并满足“升级链遵循 actor-owner-bpm-admin-human”。
- 交接说明：交接要求：将 escalation_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:trigger-schedule-runtime:p6`。该阶段采用临时 AP 语法，映射 skill 为 `sys.bpm.escalation-handler`，穿透执行策略：允许（同 Actor 场景）。

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
