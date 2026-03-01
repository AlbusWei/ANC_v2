# M5 — 自演化模块详细设计

> 版本: v0.4.0 | 建设优先级: P2

## 模块定位

M5 负责演化提案（`EvolutionProposal`）生成、排序与治理编排，构建“周期 + 事件”混合触发闭环，不替代 M3 执行与 M4 放行。

## 模块边界

1. M5 输出提案与优先级，不直接执行开发任务。
2. M5 将提案下发至 M3 实施，由 M1 执行验证，再回到 M4 做状态迁移与角色放行。
3. M5 维护演化证据链与风险回滚约束。

## 触发机制（混合触发）

1. 周期触发（保底巡检）
2. 事件触发（事故、质量下降、需求变化插队）

## 演化闭环路径

`Monitor/Analyze -> Plan -> M3 Implement -> M1 Verify -> M4 Transition`

## EvolutionProposal 最小字段

1. `proposal_id`
2. `trigger_type`（`periodic | event`）
3. `target_product_id`
4. `expected_value`
5. `verification_metrics`
6. `risk`
7. `rollback_plan`

## Fail-Closed 规则

1. 证据缺失、指标不可比时，提案不得进入实施。
2. 未定义回滚方案的高风险提案不得下发 M3。
3. 验证失败时必须触发回滚或降级，并升级到治理链路处理。

## 与双主线关系

1. 内部主线将运行反馈接入 M5，形成持续自改进。
2. 外部主线复用同一演化治理机制，保持提案与证据口径一致。

## 验收

- [ ] 混合触发（周期 + 事件）可被清晰识别
- [ ] 闭环路径覆盖 M3 Implement / M1 Verify / M4 Transition
- [ ] EvolutionProposal 字段满足可追溯与回滚要求
- [ ] fail-closed 规则在证据不足场景可执行
