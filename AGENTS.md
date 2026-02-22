# ANC v2 - AGENTS

> 本文件是所有协作者（人类、外部 Coding Agent、系统内 Agent）进入项目的第一入口。

## 1. 项目目标

ANC v2 是一个可反身自开发、可自进化的 Agentic 系统。

## 2. SSOT 与核心文档

1. 架构 SSOT：`/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md`
2. 流程 SSOT：`/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`
3. 测试方法：`/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md`
4. 上下文协议：`/Users/albus/MyProjects/ANC_v2/docs/architecture/context_protocol.md`
5. 施工平面：`/Users/albus/MyProjects/ANC_v2/docs/architecture/construction_plane.md`
6. 术语表：`/Users/albus/MyProjects/ANC_v2/docs/architecture/glossary.md`
7. OpenClaw 接口：`/Users/albus/MyProjects/ANC_v2/docs/architecture/openclaw_interface.md`
8. registry 契约：`/Users/albus/MyProjects/ANC_v2/docs/architecture/registry_contracts.md`
9. 详细设计索引：`/Users/albus/MyProjects/ANC_v2/docs/design/README.md`

## 3. 执行原则

1. 因果驱动链：`Objective -> Spec -> Test -> Development`。
2. 冲突优先级：`Objective > Spec > Test > Implementation`。
3. 文档即真相：关键结论必须落盘。
4. Fail-Closed：证据不足或协议错误时默认失败并回退。
5. Skill/Process 必须遵循 Agent Skills 规范并与 OpenClaw 配置咬合。

### 3.1 Skill/Process 工程标准入口（强制）

1. Skill 设计前必须先读：`/Users/albus/MyProjects/ANC_v2/docs/design/standards/skill-definition-standard.md`
2. Process 设计前必须先读：`/Users/albus/MyProjects/ANC_v2/docs/design/standards/process-definition-standard.md`
3. Process 设计必须满足新增硬约束：
   - 连续性约束（单复合流程不得跨非连续生命周期段）
   - phase 闭合约束（每个 phase 必须映射到已定义 AP/子流程）
   - 断点处理规则（跨断点必须拆流程，由上级流程编排）
4. Skill 命名必须满足语义约束：
   - 可复用 `skill_id` 禁止模块标记型命名（如 `m1-*`）
5. 汇总技能文档（若采用）必须为每个 `skill_id` 提供定义卡：
   - 输入契约、输出契约、Fail-Closed、test_mount（可为计划字段）

## 4. 协作约束

1. 工作空间内所有文件路径必须使用相对路径（相对仓库根目录）表达，禁止使用绝对路径作为协作输入或交付输出。
2. 若因协议说明必须使用绝对路径，或因 worktree 视角差异需要统一口径时，一律以当前目录（canonical 目录）`/Users/albus/MyProjects/ANC_v2/` 为根目录解释，并同时标注对应相对路径。
3. 跨 Agent 上下文通过文档传递，不依赖会话记忆。
4. 变更架构/流程/资产后必须同步更新对应文档与 registry。
5. 未更新施工平面的推进不视为“已完成”。

## 5. OpenClaw 操作基线

1. 配置读取：`openclaw config get agents.list --json`
2. 配置补丁：`openclaw gateway call config.patch --params '{\"raw\":\"...\",\"baseHash\":\"...\"}' --json`
3. 网关健康检查：`openclaw health --json`
4. 会话检查：`openclaw sessions --json`
5. 代理执行：`openclaw agent --message \"...\"`

### 5.1 OpenClaw 工作区/Skill 源切换（M2+ 强制）

> 目标：在主仓与各个 worktree 之间切换时，确保 OpenClaw 的 `agents` 与可加载 skill/process 源目录同步切换。

1. 进入任意运行时开发/测试前，必须先执行：
   - `python3 /Users/albus/MyProjects/ANC_v2/tools/openclaw/switch_workspace.py --repo-root <目标仓库或worktree根目录>`
2. 脚本职责（Fail-Closed）：
   - 从 `config/openclaw.phase05.with-entry.fragment.json` 解析目标 `agents.list`。
   - 同步 `agents.defaults.workspace`、`agents.defaults.repoRoot`、`agents.list`、`tools.agentToAgent.allow`。
   - 将片段中的 `skills.entries.*.source` 投影为 `skills.load.extraDirs`（兼容 OpenClaw 2026.2 配置模型）。
3. 切换后最小校验（必须通过）：
   - `openclaw config get agents.defaults.repoRoot --json`
   - `openclaw config get skills.load.extraDirs --json`
   - `openclaw skills info config-change-gatekeeper --json`（或本回合目标技能）
4. 禁止直接把 `skills.entries.<key>.source` 写入 OpenClaw 运行配置（会触发 `invalid config`）。
5. 若脚本或校验任一步失败，禁止进入运行时测试或宣告 Done。

## 6. 当前阶段边界

当前处于 Phase 0/0.5：优先构建治理骨架，不做大规模业务功能实现。

## 7. Entire 管理基线（Codex 强制）

> 目标：确保 Codex 在本仓库的每次开发变更都纳入 Entire 会话管理并可审计。

1. 任务开始前必须检查 Entire 状态：
   - `entire status --detailed`
   - 期望：`Enabled (manual-commit)`；否则执行：`entire enable --strategy manual-commit`
2. 使用 Codex 时必须走桥接脚本启动会话：
   - `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py start`
3. 每个有意义开发回合（有代码变更）后、提交前，必须执行一次同步：
   - `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py sync --prompt "<本回合需求>" --summary "<本回合实现>" --files <changed-file-1> <changed-file-2>`
4. 每次提交后必须执行校验：
   - `git log -1 --pretty=raw`
   - 提交信息中必须包含：`Entire-Checkpoint: <id>`
5. 任务结束时必须关闭桥接会话：
   - `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py end`
6. Fail-Closed：若 `start/sync/end` 任一步失败，或提交缺失 `Entire-Checkpoint`，本次任务不得宣告完成，必须先修复再继续。
7. 协议文档：
   - `/Users/albus/MyProjects/ANC_v2/docs/design/interfaces/entire-codex-sync-protocol.md`
   - `/Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/references/bridge-contract.md`

## 8. Layer/Module 联动文档门禁（新增）

> 目标：避免“module/layer 已落盘，但新增 skill/process/agent 未同步设计文档”的倒挂。

1. 触发条件（任一满足即触发门禁）：
   - 修改 `/Users/albus/MyProjects/ANC_v2/docs/design/layers/` 或 `/Users/albus/MyProjects/ANC_v2/docs/design/modules/` 下文档，且涉及职责、边界、依赖、接口变化。
   - 新增或重构 `/Users/albus/MyProjects/ANC_v2/skills/`、`/Users/albus/MyProjects/ANC_v2/processes/`、`/Users/albus/MyProjects/ANC_v2/agents/` 下资产。
2. 同回合必须完成的联动更新：
   - 受影响的设计文档：`/Users/albus/MyProjects/ANC_v2/docs/design/skills/`、`/Users/albus/MyProjects/ANC_v2/docs/design/processes/`、`/Users/albus/MyProjects/ANC_v2/docs/design/agents/`。
   - 清单文档：`/Users/albus/MyProjects/ANC_v2/docs/design/inventories/skill-inventory.md`、`/Users/albus/MyProjects/ANC_v2/docs/design/inventories/process-inventory.md`、`/Users/albus/MyProjects/ANC_v2/docs/design/inventories/agent-inventory.md`。
   - 注册表：`/Users/albus/MyProjects/ANC_v2/shared/registry/skill_registry.json`、`/Users/albus/MyProjects/ANC_v2/shared/registry/process_registry.json`、`/Users/albus/MyProjects/ANC_v2/shared/registry/agent_directory.json`。
   - 施工平面：`/Users/albus/MyProjects/ANC_v2/docs/architecture/construction_plane.md` 对应条目必须同步更新。
3. 状态门禁：
   - 新增 skill/process/agent 若缺设计文档，生命周期只能停留 `draft`，禁止推进到 `review/active`。
4. 提交前最小校验：
   - `python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify`
   - `rg -n "<asset-id>" /Users/albus/MyProjects/ANC_v2/docs/design /Users/albus/MyProjects/ANC_v2/shared/registry`
5. Fail-Closed：
   - 任一联动项缺失（设计文档、inventory、registry、施工平面）即判定任务未完成，不得宣告 Done 或合入。
