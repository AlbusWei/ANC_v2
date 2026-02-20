# M4 — 生命周期管理模块详细设计

> 版本: v0.2.0 | 建设优先级: P1

## 模块定位

管理 Agent/Skill/Process 的 5 态生命周期与审批证据。

## 状态机

`draft -> review -> active -> deprecated -> retired`

## 组件

1. lifecycle-transition
2. permission-checker
3. registry-validator
4. lifecycle-review

## 约束

1. review 前不得 active。
2. active 不得直接 retired。
3. 每次转换必须有 evidence_ref。

## 验收

- [ ] 非法状态迁移被拒绝
- [ ] 状态与 registry 同步
- [ ] 审批链完整
