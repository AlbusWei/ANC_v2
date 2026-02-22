# Aggregation Rules

优先级：

1. 任一分项 `fail` -> `gate_decision=fail`
2. 无 fail 且存在 `hold` -> `gate_decision=hold`
3. 无 fail/hold 且存在 `test_invalid` -> `gate_decision=test_invalid`
4. 其余 -> `gate_decision=pass`

补充：

- 任一关键评测包不可解析 -> `fail`
- 证据链缺失 -> `fail`
