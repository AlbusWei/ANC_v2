# L5 — 业务交付层详细设计

> 版本: v0.2.0

## 层级定位

面向外部客户交付业务价值，并将反馈回流到 L4/L3。

## 最小定义（七类）

- Agents: delivery agents 13 角色
- Skills: business skills（按域扩展）
- Processes: software-vendor-e2e-flow
- Components: delivery artifacts, acceptance packs
- Interfaces: client handoff, support feedback
- Data Models: role responsibility, acceptance schema
- Acceptance: 客户验收 + 运行反馈回流

## 双主线复用

1. 外部交付主线复用内部孵化闭环。
2. delivery-iterations 阶段必须满足内部质量门禁。

## 当前边界

本层以设计与治理规范先行，运行资产后续按生命周期逐步激活。
