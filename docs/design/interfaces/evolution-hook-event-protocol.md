# Evolution Hook Event Protocol

> 版本: v0.1.0 | 状态: draft | 适用范围: M5 自进化触发链路

## 1. 目标

定义 M5 自进化触发链路的领域事件协议，确保“生命周期事件 -> 触发运行时 -> 提案治理”全过程可追溯、可去重、可 Fail-Closed。

## 2. 双层事件模型（强制）

1. 平台层事件（platform hook）：来自 OpenClaw 内置事件，仅用于桥接原始信号。
2. 领域层事件（domain hook）：由 ANC 生命周期阶段产出，作为治理决策主信号。

治理判定只消费领域层事件；平台层事件不得直接驱动提案放行。

## 3. 领域事件命名空间

标准事件名（v0.1.0）：

1. `m1.gate.failed`
2. `m1.gate.hold`
3. `m1.gate.pass`
4. `m3.implementation.failed`
5. `m3.implementation.completed`
6. `m4.lifecycle.transition.approved`
7. `m4.lifecycle.transition.rejected`
8. `m4.lifecycle.rollback.executed`
9. `m5.proposal.rejected`
10. `m5.proposal.accepted`
11. `asset.health.degraded`
12. `asset.health.critical`

## 3.1 平台桥接事件命名空间（仅桥接，不参与治理放行）

平台层 Hook 统一使用 `platform.<type>.<action>` 事件名，当前桥接集：

1. `platform.agent.bootstrap`
2. `platform.command.new`
3. `platform.command.reset`
4. `platform.command.stop`
5. `platform.gateway.startup`

约束：

1. 平台桥接事件只用于入口可观测与追踪，不得直接作为治理放行信号。
2. 若未配置显式路由，必须走 `unmatched_event_receipt`，禁止静默丢弃。

## 4. 事件包最小契约（强制）

必填字段：

1. `event_id`：事件唯一主键。
2. `event_name`：命名空间内标准事件名（领域事件或平台桥接事件）。
3. `event_time`：RFC3339 时间戳。
4. `module`：`m1|m3|m4|m5|runtime-monitor`。
5. `trigger_source`：`platform-hook|domain-hook|heartbeat|cron`。
6. `severity`：`info|warning|critical`。
7. `evidence_ref`：可追溯证据引用。
8. `owner_agent_id`：责任主体。
9. `dedupe_key`：去重键。

对象定位字段（至少一个）：

1. `asset_ref`
2. `target_product_id`

可选字段：

1. `source_instance_id`
2. `window_bucket`
3. `trace`（扩展诊断字段）

## 5. 幂等与去重规则

1. 主键：`event_id`。
2. 回退键：`event_name + asset_ref + window_bucket + source_instance_id`。
3. 主键与回退键均不可构造或冲突不可判定时，必须 Fail-Closed。

## 6. 分发契约

1. 事件先进入 `sys.bpm.trigger-ingress-normalizer`。
2. 归一后进入 `trigger-event-runtime`（匹配、去重、分发、证据归档、补数/升级）。
3. 事件命中策略后可升级为 `AssetIssue` / `EvolutionProposal`。

## 7. 升级规则（v0.1.0）

1. `m1.gate.failed` 连续超过阈值 -> `asset.health.degraded`。
2. `m1.gate.hold` 超 SLA -> `asset.health.critical`。
3. `m4.lifecycle.rollback.executed` -> 直接 `critical` 并要求 owner 同回合审核。

## 8. Fail-Closed 规则

1. 缺 `evidence_ref`：拒绝进入提案链，仅允许补数/升级。
2. 缺 `owner_agent_id` 或不可解析：拒绝升级为 `EvolutionProposal`。
3. 去重冲突不可判定：阻断分发并触发升级。
4. 未命中策略：禁止静默丢弃，必须产出 `unmatched_event_receipt`。

## 9. OpenClaw 适配约束

1. Hook handler 必须快返回，不在 handler 内做重计算。
2. Hook handler 异常必须本地捕获，禁止外抛影响其他 handler。
3. 精确定时任务由 Cron 承担，常态巡检由 Heartbeat 承担，Hook 仅做事件入口。
