# L2 — 编排治理层详细设计

> 版本: v0.3.0

## 层级定位

- 职责: BPM 编排、生命周期治理、触发治理、权限与证据管理。
- 上层消费者: L3, L4, L5。
- 下层依赖: L1, L0。

## 最小定义（七类）

- Agents: bpm, hr
- Skills: lifecycle-transition, permission-checker, registry-validator, process-instance-manager, config-change-gatekeeper
- Processes: lifecycle-review, registry-sync, escalation, governed-config-change
- Components: process instance store, trigger matcher, trigger ledger, registry
- Interfaces: BPM↔Actor, trigger ingress, registry access, role handoff
- Data Models: process/evidence/context schema, trigger policy schema (planned)
- Acceptance: 编排正确性、门禁正确性、触发幂等正确性、恢复可用性

## 触发治理边界

1. M2 负责触发运行时（匹配、去重、调度、补跑、证据归档）。
2. M4 负责触发策略治理（策略生命周期、owner override、风险分级）。
3. 外部事件必须先归一化为内部 canonical event 后再进入 BPM 匹配。
4. App 层与 owner 不能直达 admin，必须走 BPM 升级链。

## 关键门禁

1. 无 objective/spec/test 断链不得进入实现或发布。
2. lifecycle 仅允许合法状态迁移。
3. 证据缺失默认 Fail-Closed。
4. 无法判断风险等级时按高风险处理并升级 admin。
5. 高风险系统写操作必须由 admin 审批并执行，BPM 不得代执行。

## 当前测试提案锚点

触发治理测试提案见：
`../review-layers-modules/docs/design/modules/trigger-governance-test-proposal.md`
