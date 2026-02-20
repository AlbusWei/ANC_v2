# M5 — 自演化模块详细设计

> 版本: v0.2.0 | 建设优先级: P2

## 模块定位

以指标驱动持续改进，形成监控->分析->规划->开发->验证闭环。

## 组件

1. monitor
2. analyst
3. planner
4. evolution-loop
5. improvement-review

## 与双主线关系

1. 内部主线将运行反馈接入 M5。
2. 外部主线的 support-and-feedback 复用 M5 改进机制。

## 验收

- [ ] 提案可量化
- [ ] 改进可回滚
- [ ] 指标提升可验证
