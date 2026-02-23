# agent-creator Fail-Closed 矩阵

| 错误类型 | 触发条件 | 处理动作 | 返回码 |
|---|---|---|---|
| `missing_required_fields` | 缺失 `agent_id/role_scope/interfaces/owner` 任一项 | 阻断并返回缺失字段列表 | 2 |
| `invalid_agent_id` | 命名不符合 kebab-case | 阻断并要求修正命名 | 2 |
| `invalid_interfaces` | `interfaces` 为空或缺 `protocol_ref` | 阻断并返回无效条目 | 2 |
| `owner_mismatch` | owner 与 registry 不匹配 | 阻断并提示 owner 映射失败 | 2 |
| `unexpected_error` | 运行期未捕获异常 | 中止并记录异常栈摘要 | 1 |
