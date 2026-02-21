# P4 End-to-End Delivery Flows

> 版本: v0.4.0 | 层级: P4

## 定位

定义可执行的端到端流程，直接被 BPM 编排。

## 样板流程

1. internal-productization-e2e-flow
2. software-vendor-e2e-flow
3. quality-gate-preparation
4. quality-gate-evaluation
5. hold-governance

## 规范绑定

1. 开发闭环义务与条件触发规则以 `/Users/albus/MyProjects/ANC_v2/docs/design/processes/development-loop-core-standard.md` 为真相源。
2. 样板流程用于参考映射，不承担规范真相职责。
3. 统一追溯表：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/p4-p6-obligation-traceability-matrix.md`。

## 复用规则

1. `software-vendor-e2e-flow` 的 `delivery-iterations` 必须覆盖开发闭环标准义务（核心强制 + 条件触发），并组合 `internal-productization` 的开发闭环。
2. `internal-productization` 可作为参考映射，但不是唯一复用目标。
3. 流程节点可组合 P5/P6 子流程。
4. `phase` 只能引用子流程；skill 必须先包装为原子流程。
5. 质量门禁场景必须按连续性拆分复用：`quality-gate-preparation -> AP-006 -> quality-gate-evaluation`。
6. HOLD 路由统一复用 `hold-governance`。

## 验收

- [ ] 两条主线均有端到端阶段定义
- [ ] 可追溯到 P6 原子流程
- [ ] 义务覆盖判定与条件触发规则可追溯到标准文档
- [ ] 复合流程不跨非连续生命周期断点
