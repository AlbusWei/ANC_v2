# objective-writer Fail-Closed 边界

| 边界项 | 判定条件 | 处理策略 |
|---|---|---|
| 可测性边界 | 成功标准不可验证 | 拒绝产出并返回不可测条目 |
| 范围边界 | 缺失 scope/non-goals | 拒绝推进 Spec 阶段 |
| 冲突边界 | 与 SSOT 或上级约束冲突 | 标记冲突并回退到需求澄清 |

## 审查建议

1. 优先检查 `success_criteria` 是否可被测试资产消费。
2. 检查 `scope_baseline` 是否覆盖主链路与异常链路。
3. 冲突未解决时禁止推进生命周期。
