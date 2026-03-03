# Owner Evolution Governance Process

> 版本: v0.1.0 | 层级: P4 | 类型: 复合流程（规划） | process_id: owner-evolution-governance

## 目标

把“资产 owner 运营责任”转化为可执行治理闭环，确保每个资产都能基于运行信号形成提案、执行验证并完成生命周期收口。

闭环主链：

`M5 proposal -> M3 implement -> M1 verify -> M4 transition`

## 连续性边界

1. 本流程负责提案治理与下游门禁编排，不承接具体业务实现细节。
2. 生命周期迁移执行权由 `hr` 保持，不在本流程内重定义迁移权限。
3. 触发链路统一复用 `trigger-ingress-normalizer -> trigger-event-runtime`，禁止旁路。

## 触发模型（混合触发）

1. Hook：事件入口（平台桥接 + 领域事件主信号）。
2. Heartbeat：常态巡检（健康监控与批处理）。
3. Cron：精确定时评审（独立会话重分析、提醒/注入）。

领域事件协议：`docs/design/interfaces/evolution-hook-event-protocol.md`  
事件数据模型：`docs/design/data-models/evolution-hook-event-schema.json`

## 阶段定义（目标态）

1. `p1 health-intake`
2. `p2 proposal-drafting`
3. `p3 governance-review`
4. `p4 implementation-dispatch`
5. `p5 quality-verify`
6. `p6 lifecycle-transition`
7. `p7 retro-close`

## 输入契约（目标态）

1. `trigger_receipt_ref`
2. `asset_operation_profile_ref`
3. `asset_health_snapshot_ref`
4. `asset_issue_ref`（可选）
5. `owner_commitment_ref`
6. `rollback_policy_ref`
7. `verification_metric_refs`

## 输出契约（目标态）

1. `evolution_proposal_ref`
2. `m3_execution_ref`
3. `m1_verification_ref`
4. `m4_transition_ref`
5. `evolution_execution_record_ref`
6. `owner_review_minutes_ref`

## Fail-Closed 规则

1. 无 `owner_agent_id` 或不可解析：阻断提案创建。
2. 无 `rollback_policy_ref`：高风险提案不得下发 M3。
3. 指标不可比或证据不可追溯：阻断治理评审。
4. `m1_verification` 非 `pass`：不得进入 M4 迁移。
5. 事件去重冲突不可判定：阻断分发并触发升级。

## 证据落盘规范

1. `runtime_data/evolution/operation-profiles/`
2. `runtime_data/evolution/health-snapshots/`
3. `runtime_data/evolution/issues/`
4. `runtime_data/evolution/proposals/`
5. `runtime_data/evolution/executions/`
6. `runtime_data/evolution/reviews/`

## 过渡执行映射（Phase 1）

在专职演化流程未注册前，允许映射：

1. 观测与归因：`system-analyst + sys.arch.system-feedback-digest`
2. 提案与计划：`evolution-feedback-planning`
3. 实施：`full-development`（或 `hotfix/refactor`）
4. 验证：`quality-gate-evaluation`
5. 迁移：`lifecycle-review`

## 当前状态

1. 设计已落盘，流程资产尚未注册到 `process_registry`。
2. 生命周期状态目标：`draft`（待 Batch 实施后再推进）。
