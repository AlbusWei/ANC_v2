# ANC v2 与 OpenClaw 接口契约

最后更新：2026-02-18  
版本：2.0.0-alpha

> 本文件将 ANC v2 的架构约束映射到 OpenClaw 的配置模型与 CLI 接口，避免“文档设计与运行时脱节”。

## 1. 目标

1. 明确 ANC 配置如何落到 OpenClaw Gateway 配置。
2. 明确 ANC 运维动作对应的 OpenClaw CLI 命令。
3. 明确 Skill/Process 如何遵循 Agent Skills 规范并被 OpenClaw 加载。

## 2. Gateway 配置契约

### 2.1 配置变更验证

1. 启用严格验证：`gateway.config.validation.strict=true`。
2. 配置热更新模式可用值：`startup`, `manual`, `watch`。
3. 生产建议：`manual`，通过显式指令触发更新。

### 2.2 配置变更接口（Config RPC）

OpenClaw Gateway 提供配置 RPC：

1. 读取当前配置：

```bash
openclaw gateway call config.get '{}'
```

2. 应用完整配置（全量替换）：

```bash
openclaw gateway call config.apply '{"config": {...}}'
```

3. 局部补丁（推荐，最小变更）：

```bash
openclaw gateway call config.patch '{
  "ops": [
    {"op": "replace", "path": "/defaultModel", "value": "claude-sonnet-4.5"}
  ]
}'
```

### 2.3 可热更新片段（核心）

以下配置片段适合通过 `config.patch` 动态更新：

1. `global`
2. `defaultAgent`
3. `defaultModel`
4. `tools`
5. `channels`
6. `channelsConfig`
7. `agents`
8. `skills`

非上述片段变更应通过重启生效：`openclaw gateway restart`。

## 3. CLI 运行接口（ANC 施工常用）

### 3.1 初始化与体检

```bash
openclaw onboard --install-daemon
openclaw doctor --fix
openclaw health --json
```

### 3.2 配置管理

```bash
openclaw configure
openclaw config get --json
openclaw config set <path> <value>
openclaw config unset <path>
```

### 3.3 Gateway 生命周期

```bash
openclaw gateway --port 18789
openclaw gateway service install
openclaw gateway service restart
openclaw gateway restart
```

### 3.4 Channel 与 Agent 管理

```bash
openclaw channels add <name> --sdk <sdk>
openclaw channels list
openclaw channels login <name>

openclaw agents add <agent-id>
openclaw agents list
openclaw agents get <agent-id>
openclaw agents delete <agent-id>
```

### 3.5 会话与执行

```bash
openclaw sessions --json
openclaw session show <session-id>
openclaw agent --message "..."
openclaw run --message "..."
```

## 4. Skills 加载契约（OpenClaw 对齐）

OpenClaw `skills` 关键配置字段：

1. `skills.entries[]`: 声明技能目录或单体条目。
2. `skills.allowBundled`: 是否允许内置技能。
3. `skills.load.disable`: 禁用自动发现（默认 false）。
4. `skills.install.strategy`: `all` 或 `lazy`。
5. `skills.install.preferBrew`: 优先使用 Homebrew 安装依赖。

建议策略：

1. Phase 0/1 保持 `skills.install.strategy=lazy`，降低冷启动成本。
2. 将 ANC 自有技能明确写入 `skills.entries`，避免隐式扫描漂移。

## 5. AGENTS 模板契约（OpenClaw 对齐）

参考 OpenClaw 默认模板，Agent 至少应包含：

1. `SOUL.md`
2. `USER.md`
3. `TOOLS.md`
4. `IDENTITY.md`
5. `AGENTS.md`
6. `MEMORY.md`
7. `memory/YYYY-MM-DD.md`（日记忆）

ANC 要求：Kernel/Control/App 三层 Agent 均按该模板落盘，并在 registry 可发现。

## 6. Process 作为 Skill 的落地约束

1. 每个 process 目录必须包含 Agent Skills 规范兼容的 `SKILL.md`。
2. 流程结构化定义放在 `process.json`（或 `process.yaml`）中。
3. `SKILL.md` 负责被 OpenClaw 识别；`process.json` 负责被 BPM 解释执行。

## 7. 变更工作流（建议）

1. 先在 `system_overview.md`/`process_architecture.md` 更新架构规则。
2. 再更新 registry 和模板。
3. 最后通过 OpenClaw CLI 执行配置或运行验证。
4. 所有变更写入 `construction_plane.md` 与证据路径。

## 8. 参考链接

1. OpenClaw 文档首页：https://docs.openclaw.ai/
2. Gateway Configuration：https://docs.openclaw.ai/gateway/configuration
3. OpenClaw CLI：https://docs.openclaw.ai/cli/index
4. OpenClaw AGENTS 模板：https://docs.openclaw.ai/reference/templates/AGENTS
5. Agent Skills 规范：https://agentskills.io/specification
