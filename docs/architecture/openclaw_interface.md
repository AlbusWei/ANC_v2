# ANC v2 与 OpenClaw 接口契约

最后更新：2026-02-20  
版本：2.0.2-alpha

> 本文件将 ANC v2 架构约束映射到 OpenClaw 的配置与 CLI 接口，确保设计可落到运行时。
> 本文件命令示例已在本机 OpenClaw `2026.2.9` 环境做基础可用性校验（只执行读取或空补丁验证）。

## 1. 目标

1. 明确 ANC 资产如何映射到 OpenClaw Gateway 配置。
2. 明确 ANC 运维动作对应的 OpenClaw CLI 命令。
3. 明确 Skill/Process 如何遵循 Agent Skills 规范并被 OpenClaw 加载。

## 2. Gateway 配置契约

### 2.1 配置校验与重载

1. Gateway 配置采用严格验证（配置错误会被拒绝）。
2. `gateway.reload.mode` 可选：`hybrid`, `hot`, `restart`, `off`。
3. 推荐：开发用 `hybrid`，生产用 `restart` 或受控 `hybrid`。

### 2.2 Config RPC（经 `openclaw gateway call`）

读取配置：

```bash
openclaw gateway call config.get --params '{}' --json
```

说明：返回结果包含 `hash`，用于并发安全更新。

补丁更新（JSON Merge Patch）：

```bash
openclaw gateway call config.patch --params '{
  "raw": "{\"skills\":{\"entries\":{\"anc-v2-meta\":{\"source\":\"/Users/albus/MyProjects/ANC_v2/skills/meta\"}}}}",
  "baseHash": "<hash-from-config.get>"
}' --json
```

全量更新：

```bash
openclaw gateway call config.apply --params '{"raw":"<full-json-string>","baseHash":"<hash>"}' --json
```

### 2.3 热更新边界

根据 Gateway Configuration 文档：

1. 以下类别通常支持热更新：channels、agents/models、automation、sessions、tools/media、UI/misc。
2. 以下变更通常需要重启：`gateway.*`、discovery、canvas host、plugins（部分例外）。

遇不确定情况，统一执行：

```bash
openclaw gateway restart
```

## 3. CLI 运行接口（ANC 常用）

### 3.1 初始化与健康检查

```bash
openclaw onboard --install-daemon
openclaw doctor --fix
openclaw health --json
```

### 3.2 配置管理

```bash
openclaw configure
openclaw config get agents.list --json
openclaw config get skills.install --json
openclaw config set <path> <value>
openclaw config unset <path>
```

### 3.2.1 ANC 治理约束（配置写路径）

1. 读取类命令（`config get`、`gateway call config.get`）可由 admin、bpm、personal-assistant 在各自权限范围内执行。
2. 系统级写命令（`config set`、`config unset`、`gateway call config.patch`、`gateway call config.apply`）默认必须走：
   - `requester -> BPM 审批门禁 -> admin 执行 -> BPM 归档`
3. App 层 Agent 一律不允许直接执行系统级写命令。
4. Kernel 层 Agent 仅在“白名单 + 幂等 + 低风险”条件下允许直接执行，且必须由 BPM 记录变更单与执行证据。
5. 所有写操作必须带 `baseHash` 并产出前后 hash、补丁摘要、回滚结果。

### 3.3 Gateway 生命周期

```bash
openclaw gateway install
openclaw gateway start
openclaw gateway status
openclaw gateway restart
openclaw gateway stop
```

### 3.4 Channel 与 Agent 管理

```bash
openclaw channels add
openclaw channels list
openclaw channels login
openclaw channels status --deep

openclaw agents add
openclaw agents list
openclaw agents delete
```

### 3.5 会话与执行

```bash
openclaw sessions --json
openclaw agent --message "..."
openclaw message send --target <target> --message "..."
```

## 4. Skills 加载契约（OpenClaw 对齐）

OpenClaw `skills` 关键配置字段（以配置文档为准）：

1. `skills.entries`：技能入口映射（对象结构）。
2. `skills.allowBundled`：是否允许内置技能。
3. `skills.install.nodeManager`：依赖安装器（如 `npm`）。
4. `skills.install.preferBrew`：优先 Homebrew 安装依赖。

建议：

1. 将 ANC 自有技能显式声明到 `skills.entries`，避免隐式扫描漂移。
2. 在 Phase 0/1 优先按目录入口加载 `skills/meta` 与 `processes/meta`。

## 5. AGENTS 模板契约（OpenClaw 对齐）

参考 OpenClaw AGENTS 模板，Agent 至少应包含：

1. `SOUL.md`
2. `USER.md`
3. `TOOLS.md`
4. `IDENTITY.md`
5. `AGENTS.md`
6. `MEMORY.md`
7. `memory/YYYY-MM-DD.md`

ANC 要求：Kernel/Control/App 三层 Agent 均按模板落盘，并可在 registry 查询。

## 6. Process 作为 Skill 的落地约束

1. 每个流程目录必须有 Agent Skills 兼容 `SKILL.md`（frontmatter）。
2. 流程结构化定义必须存放在 `process.json` 或 `process.yaml`。
3. `SKILL.md` 给 OpenClaw 加载，`process.json` 给 BPM 执行。

## 7. Phase 0.5 配置片段

本仓库提供 Phase 0.5 配置片段：

`/Users/albus/MyProjects/ANC_v2/config/openclaw.phase05.fragment.json`

可选入口代理版本：

`/Users/albus/MyProjects/ANC_v2/config/openclaw.phase05.with-entry.fragment.json`

用途：

1. 映射 ANC_v2 的 `agents.list` 基线。
2. 映射 ANC_v2 的 `skills.entries` 基线。
3. `with-entry` 片段会将 `personal-assistant` 纳入默认 `agents.list`。
4. 片段写入全局 OpenClaw 配置前，需评估对现有工作区（如 ANC v1）的影响。

## 8. 变更工作流（建议）

1. 先更新 SSOT 文档（架构/流程/契约）。
2. 再更新 registry 与模板。
3. 涉及系统级配置写操作时，先由 BPM 完成审批门禁，再由 admin 执行变更。
4. 再应用 OpenClaw 配置（`config set` 或 `gateway call config.patch`）。
5. 最后写入施工平面和证据路径。

## 9. 参考链接

1. OpenClaw 文档首页：https://docs.openclaw.ai/
2. Gateway Configuration：https://docs.openclaw.ai/gateway/configuration
3. OpenClaw CLI：https://docs.openclaw.ai/cli/index
4. OpenClaw AGENTS 模板：https://docs.openclaw.ai/reference/templates/AGENTS
5. Agent Skills 规范：https://agentskills.io/specification
