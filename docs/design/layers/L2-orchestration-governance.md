# L2 — 编排治理层详细设计

> 版本: v0.2.0

## 层级定位

- 职责: BPM 编排、生命周期治理、权限与证据管理。
- 上层消费者: L3, L4。
- 下层依赖: L1, L0。

## 最小定义（七类）

- Agents: bpm, hr
- Skills: lifecycle-transition, permission-checker, registry-validator, process-instance-manager
- Processes: lifecycle-review, registry-sync, escalation
- Components: process instance store, registry
- Interfaces: BPM↔Actor, registry access, role handoff
- Data Models: process/evidence/context schema
- Acceptance: 编排正确性、门禁正确性、恢复可用性

## 关键门禁

1. 无 objective/spec/test 断链不得进入实现或发布。
2. lifecycle 仅允许合法状态迁移。
3. 证据缺失默认 Fail-Closed。
