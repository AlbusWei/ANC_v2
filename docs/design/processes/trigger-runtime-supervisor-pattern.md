# Trigger Runtime Supervisor Pattern

> 版本: v0.1.0 | 层级: P5 | 类型: 子流程模式 | process_id: trigger-runtime-supervisor（可选）

## 模式定位

`trigger-runtime-supervisor` 是上级路由模式流程，不直接执行业务或证据归集，负责把触发请求按类型分派到对应 P4 运行流程。

## 适用条件

1. 触发家族超过 2 类且持续扩展。
2. 跨触发公共治理逻辑明显增厚（统一熔断、统一 backpressure、统一审计聚合）。
3. 需要统一入口策略而不改变下游 P4 流程契约。

## 路由策略

1. `schedule|heartbeat` -> `trigger-schedule-runtime`
2. `event|threshold` -> `trigger-event-runtime`（可按策略再细分）

## 输入契约（模式级）

1. `trigger_type`
2. `canonical_trigger_ref`
3. `routing_policy_ref`
4. `catchup_policy_ref`
5. `dedupe_policy_ref`

## 输出契约（模式级）

1. `routed_process_id`
2. `route_decision_ref`
3. `route_evidence_ref`

## Fail-Closed

1. 路由策略不可解析 -> `fail`
2. 目标流程未注册或状态不可执行 -> `fail`
3. 路由决策与输入契约不一致 -> `fail`

## 说明

1. 当前阶段保持“可选模式”，不强制引入执行资产。
2. 若未来引入执行资产，应新增对应 `process.json` 并注册到 `process_registry`。
