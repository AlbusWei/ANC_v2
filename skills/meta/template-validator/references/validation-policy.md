# template-validator 校验策略

## 校验级别

1. `strict`：任一 warning 升级为 fail。
2. `standard`：仅阻断 error。
3. `lenient`：保留 warning，不阻断。

## 决策规则

1. 存在 `blocking_issues` 则 `gate_decision=fail`。
2. 所有问题关闭后才允许进入 review。
3. 报告必须包含证据引用路径。
