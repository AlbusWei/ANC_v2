# llm-judge verdict schema

## 必填字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `pass` | boolean | 是否通过 |
| `confidence` | number | 置信度，范围 `[0,1]` |
| `remarks` | string/array | 判定依据 |
| `suggestions` | array | 改进建议 |
| `traceability` | object | 证据映射 |

## 结构约束

1. `pass=false` 时 `suggestions` 至少 1 条。
2. `traceability` 必须包含 `objective_ref/spec_ref/actual_output_ref`。
