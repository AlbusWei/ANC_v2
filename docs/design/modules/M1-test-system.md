# M1 — 测试系统模块详细设计

> 版本: v0.2.0 | 建设优先级: P0

## 模块定位

提供 Objective/Subjective 双轨评估、回归执行和发布门禁。

## 组件

1. llm-judge
2. test-designer
3. regression-runner
4. TEST 模板体系

## 关键流程挂载

- AP-005 test-design
- AP-007 objective-evaluation
- AP-008 subjective-evaluation
- AP-009 regression-execution

## 验收

- [ ] 结构化 verdict 输出稳定
- [ ] 回归失败可阻断发布
- [ ] 测试结果可回写 lifecycle-review
