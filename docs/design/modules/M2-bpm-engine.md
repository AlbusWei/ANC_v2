# M2 — BPM 引擎模块详细设计

> 版本: v0.3.0 | 建设优先级: P0

## 模块定位

流程编排中枢，负责流程运行时、触发运行时和证据链治理。

关键边界：

1. M2 只负责运行时编排，不负责触发策略生命周期管理。
2. M2 不持有系统级高权限写操作能力。
3. 涉及系统级写操作时，固定由 admin 执行，M2 负责门禁与编排留痕。

## 组件

1. process parser
2. instance manager
3. scheduler
4. evidence recorder
5. recursion lineage guard
6. trigger ingress normalizer
7. trigger matcher + dedupe ledger
8. catchup scheduler
9. escalation handler

## 递归能力

1. 支持 parent/child 实例隔离。
2. 支持 `parent_instance_id`, `lineage_ref`, `stack_depth`。
3. 超深度递归触发 Fail-Closed。

## 触发运行时能力

1. 支持 `schedule|heartbeat|event|threshold` 触发类型。
2. 外部事件先标准化为内部 canonical event，再执行匹配。
3. 去重采用混合策略：优先 `source+event_id`，缺失回退业务语义键。
4. 漏跑采用补跑优先：`catchup_window` 内自动补跑，超窗升级 owner。

最小事件字段：

1. `event_id`
2. `event_time`
3. `entity_type`
4. `entity_id`
5. `from_status`
6. `to_status`
7. `evidence_ref`
8. `emitted_by`
9. `instance_id`

## Fail-Closed 与安全约束

1. 触发输入字段缺失或证据不可达时拒绝执行。
2. 去重键冲突且无法判定时拒绝执行并升级。
3. 风险无法判定时按高风险处理并升级 admin。
4. App/owner 请求不得直达 admin，必须走 BPM 升级链。

## 验收

- [ ] P4 流程可组合 P5/P6 并执行
- [ ] 父子实例不共享可变上下文
- [ ] 证据链完整
- [ ] 3 分钟定时触发在异常时推送、无异常仅记账（设计提案）
- [ ] Skill `review -> active` 事件触发证据归集且去重生效（设计提案）

测试提案文档：
`../review-layers-modules/docs/design/modules/trigger-governance-test-proposal.md`
