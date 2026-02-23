# objective-writer 目标模板模式

## 推荐结构

1. `objective_ref`
2. `objective_statement`
3. `scope_baseline`
4. `success_criteria`
5. `non_goals`
6. `risks`

## 编写规范

1. 目标陈述只描述结果，不描述实现方案。
2. 成功标准必须可观察、可计数、可复测。
3. `non_goals` 必须明确排除范围，防止范围蔓延。

## 常见反模式

1. 只写愿景，不写可测标准。
2. scope 与 non-goals 重叠或互相矛盾。
3. 缺少风险与回退边界说明。
