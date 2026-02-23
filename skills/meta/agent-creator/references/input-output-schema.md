# agent-creator 输入输出契约图

## 输入字段（最小集）

| 字段 | 类型 | 说明 |
|---|---|---|
| `agent_id` | string | 目标 Agent 标识，kebab-case |
| `role_scope` | object | 职责与边界说明 |
| `interfaces` | array | 对外/对内接口引用集合 |
| `owner` | string | 生命周期 owner |

## 输出字段（最小集）

| 字段 | 类型 | 说明 |
|---|---|---|
| `agent_doc_path` | string | Agent 设计文档路径 |
| `tools_doc_path` | string | 工具清单文档路径 |
| `registry_patch_plan` | object | 注册表补丁计划 |

## 兼容约束

1. 所有路径必须是仓库相对路径。
2. `registry_patch_plan.tests.test_doc` 必须指向有效 `TEST.md`。
3. owner 必须与现有 agent 目录或 registry 记录一致。
