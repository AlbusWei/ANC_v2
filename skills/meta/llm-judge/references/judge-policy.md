# llm-judge 判定策略

## 核心原则

1. 先验证输入证据完整性，再给 verdict。
2. 证据不可读时必须 Fail-Closed。
3. 不允许仅依据关键词匹配给出通过结论。

## 失败分类

- `missing_required_fields`
- `unresolvable_refs`
- `invalid_verdict_payload`
- `unexpected_error`
