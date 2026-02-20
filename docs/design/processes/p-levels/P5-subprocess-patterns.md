# P5 Subprocess Patterns

> 版本: v0.2.0 | 层级: P5

## 定位

沉淀可复用的子流程模式，作为 P4 组装件。

## 模式库

1. causal-drive-chain
2. approval-gate
3. loop-on-failure
4. escalation-chain
5. baseline-change-regression

## 组合约束

1. 模式可同层组合。
2. 组合后必须显式声明终止条件。
3. 每个模式都要映射到至少一个 P6 原子流程。

## 验收

- [ ] 模式与 process-patterns 一致
- [ ] 每个模式有失败处理定义
