# [Agent Name] - AGENTS

## Startup Read Order

1. `SOUL.md`
2. `USER.md`
3. `TOOLS.md`
4. `IDENTITY.md`
5. `MEMORY.md`
6. `runtime_data/agent-memory/<agent-id>/YYYY-MM-DD.md` (today and previous day)

## Upstream

[who assigns tasks]

## Downstream

[who receives outputs]

## Collaboration Rules

1. 必须遵循项目 SSOT 与流程 SSOT。
2. 跨 Agent 上下文通过文档路径传递。
3. 执行结果必须落盘并提供 `evidence_ref`。
4. 超出权限或能力范围时升级到 Owner/BPM。
5. 运行产物（含 output/evidence/业务数据/临时日志）默认写入 `runtime_data/`，不得默认写入版本控制目录。
