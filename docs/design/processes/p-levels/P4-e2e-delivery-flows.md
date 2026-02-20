# P4 End-to-End Delivery Flows

> 版本: v0.2.0 | 层级: P4

## 定位

定义可执行的端到端流程，直接被 BPM 编排。

## 样板流程

1. internal-productization-e2e-flow
2. software-vendor-e2e-flow

## 复用规则

1. `software-vendor-e2e-flow` 的 `delivery-iterations` 必须组合 `internal-productization` 的开发闭环。
2. 流程节点可组合 P5/P6 子流程。

## 验收

- [ ] 两条主线均有端到端阶段定义
- [ ] 可追溯到 P6 原子流程
