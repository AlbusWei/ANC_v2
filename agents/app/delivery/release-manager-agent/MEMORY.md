# Release-Manager-Agent - MEMORY

## Persistent Notes

1. 生命周期状态上限遵循当前回合治理约束，不可越级推进 `active`。
2. 每次发布决策都必须可回放并可追溯到输入证据。

## Storage

1. 日常执行记忆与临时日志写入 `runtime_data/agent-memory/release-manager-agent/`。
2. 仅保留可公开、可复用的长期治理规则在本文件。
