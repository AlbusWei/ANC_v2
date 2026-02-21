# Registry 读写协议

> 版本: v0.3.0 | SSOT 上游: [registry_contracts.md](../../architecture/registry_contracts.md)

## 概述

定义三表 registry（agent_directory, skill_registry, process_registry）的读写规则与投影流程。

架构决策背景见：

`/Users/albus/MyProjects/ANC_v2/docs/architecture/registry_governance_decisions.md`

## 读取协议

### 谁可以读

所有 Agent 可读取所有 registry 数据。

### 读取方式

直接读取 JSON 文件：

`shared/registry/{registry_name}.json`

### 缓存策略

不缓存。每次按需读取文件，保证读取最新状态。

## 写入协议

### 谁可以写

| Registry | 写入权限 |
|---|---|
| agent_directory.json | admin, hr |
| skill_registry.json | hr, architect (新建时) |
| process_registry.json | hr, bpm (新建时) |

### 写入流程（强制）

1. 编辑 registry 条目与 `entry_contract`。
2. 执行 `registry_contract_tool.py validate`。
3. 更新对应 `SKILL.md` 的 Capability Contract（若为 skill 资产）。
4. 执行 `registry_contract_tool.py generate-docs`（更新人类可读 schema）。
5. 执行 `registry_contract_tool.py project-openclaw --all`（更新受管配置区）。
6. 执行 `registry_contract_tool.py verify`（最终一致性校验）。

### 写入约束

1. `entry_contract.additionalProperties` 必须是 `false`。
2. 不可修改不可变 ID：`agent_id/skill_id/process_id`。
3. `version` 变更必须遵循 SemVer。
4. `status` 变更必须遵循统一生命周期状态机。
5. `agentskills.name` 必须等于 `entries[].name`。
6. pin 模式下 `openclaw.entry_key` 必须分别等于 `skill_id` / `process_id`。
7. `skills/**/SKILL.md` 必须包含 `Capability Contract (Machine-Readable)` YAML 块。
8. 对已注册 skill，`SKILL.md` 中 `test_mount` 必须与 registry `tests` 一致。

## 投影协议（Registry -> OpenClaw）

受管区：

1. `agents.list`
2. `skills.entries`

非受管区（例如 `channels`/`channelsConfig`）不被投影工具覆盖。

状态门禁：

1. agent：`draft/review/active` 可投影。
2. skill/process：默认 `review/active`。
3. draft skill/process 仅在 `openclaw.allow_draft_projection=true` 时可投影。

冲突优先级：

1. 支持 `bundle + pin`。
2. 同时命中时 pin 优先。

## 错误处理

| 错误 | 处理 |
|---|---|
| schema 违规或未知字段 | 拒绝写入（Fail-Closed） |
| 路径不存在 | 拒绝写入并报告缺失路径 |
| frontmatter 快照不一致 | 拒绝写入并报告字段冲突 |
| owner 引用不存在 | 拒绝写入并报告引用错误 |
| channel 引用不可达 | 拒绝投影并报告缺失 channel |
| 并发冲突 | 后写入者必须重新读取并合并 |

## 本地与 CI 门禁

1. pre-commit：`registry_contract_tool.py verify`。
2. CI：调用 `shared/registry/run_contract_checks.sh` 或直接执行 `verify`。
