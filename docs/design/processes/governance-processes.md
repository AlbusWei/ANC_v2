# 治理流程清单与设计

> 版本: v0.2.0 | 分类: Governance Processes

## 核心治理流程

1. lifecycle-review
2. registry-sync
3. escalation

## lifecycle-review

阶段：

1. validate-request
2. check-prerequisites
3. quality-gate
4. execute-transition
5. sync-registry

状态规则：`draft -> review -> active -> deprecated -> retired`

## escalation

升级链：`actor -> owner -> bpm -> admin -> human`

## Fail-Closed

1. 无权限或证据不足直接拒绝。
2. 状态迁移非法直接拒绝。
3. registry 不一致直接阻断。
