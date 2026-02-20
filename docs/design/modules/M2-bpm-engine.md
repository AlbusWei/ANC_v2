# M2 — BPM 引擎模块详细设计

> 版本: v0.2.0 | 建设优先级: P0

## 模块定位

流程编排中枢，支持递归流程执行与证据链治理。

## 组件

1. process parser
2. instance manager
3. scheduler
4. evidence recorder
5. recursion lineage guard

## 递归能力

1. 支持 parent/child 实例隔离。
2. 支持 `parent_instance_id`, `lineage_ref`, `stack_depth`。
3. 超深度递归触发 Fail-Closed。

## 验收

- [ ] P4 流程可组合 P5/P6 并执行
- [ ] 父子实例不共享可变上下文
- [ ] 证据链完整
