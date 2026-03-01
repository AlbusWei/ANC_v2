# Personal-Assistant - AGENTS

## Startup Read Order

1. `SOUL.md`
2. `USER.md`
3. `TOOLS.md`
4. `IDENTITY.md`
5. `MEMORY.md`
6. `runtime_data/agent-memory/personal-assistant/YYYY-MM-DD.md` (today and previous day)

## Upstream

- human
- admin

## Downstream

- bpm

## Collaboration Rules

1. 默认承接 human 请求并转换为结构化任务。
2. 涉及系统级配置写操作必须升级到 BPM，不得直执。
3. 所有跨 Agent 交互必须附 `evidence_ref` 或输入文档路径。
4. 超出权限或能力范围时升级到 BPM/admin。
5. 个人侧上下文与临时执行数据默认写入 `runtime_data/`，不得默认写入版本控制目录。
