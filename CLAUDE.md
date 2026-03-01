# ANC v2 - CLAUDE

> 本文件基于 `AGENTS.md`，作为 Claude/Coding Agent 在本仓库协作的执行入口。

## 1. 项目目标

ANC v2 是一个可反身自开发、可自进化的 Agentic 系统。

## 2. 开工前必读（SSOT）

1. `docs/architecture/system_overview.md`
2. `docs/architecture/process_architecture.md`
3. `docs/architecture/test_methodology.md`
4. `docs/architecture/context_protocol.md`
5. `docs/architecture/construction_plane.md`
6. `docs/architecture/glossary.md`
7. `docs/architecture/openclaw_interface.md`
8. `docs/architecture/registry_contracts.md`
9. `docs/design/README.md`
10. `docs/architecture/release_isolation_policy.md`
11. `docs/architecture/release_packaging_sop.md`

## 3. 执行总原则（强制）

1. 因果链必须遵循：`Objective -> Spec -> Test -> Development`。
2. 冲突优先级：`Objective > Spec > Test > Implementation`。
3. 文档即真相：关键结论必须落盘。
4. Fail-Closed：证据不足/协议错误时默认失败并回退。
5. Skill/Process 必须遵循标准并与 OpenClaw 配置咬合。

## 4. Skill / Process 设计门禁（强制）

### 4.1 标准入口

- Skill 设计前必须阅读：`docs/design/standards/skill-definition-standard.md`
- Process 设计前必须阅读：`docs/design/standards/process-definition-standard.md`

### 4.2 Process 硬约束

- 连续性约束：单复合流程不得跨非连续生命周期段。
- phase 闭合约束：每个 phase 必须映射到已定义 AP/子流程。
- 断点处理规则：跨断点必须拆流程并由上级流程编排。

### 4.3 Skill 命名与定义约束

- 可复用 `skill_id` 禁止模块标记型命名（如 `m1-*`）。
- 汇总技能文档（若采用）必须为每个 `skill_id` 提供定义卡：输入契约、输出契约、Fail-Closed、test_mount（可为计划字段）。

## 5. 输出质量与可用性（强制）

1. 默认中文输出：交付、设计文档、代码注释使用中文；英文关键字/协议字段需补充中文说明。
2. 注释强调意图、约束、边界条件、Fail-Closed 分支与关键取舍，避免噪声注释。
3. 测试汇报必须有自然语言结论（目标、覆盖范围、关键现象、风险判断、准入结论），不能只贴日志。
4. TDD 必须证明业务可用性：关键链路可运行、异常路径可恢复/可回退、Fail-Closed 生效、核心场景可复现。

## 6. 协作约束（强制）

1. 路径表达统一使用相对路径（相对仓库根目录）。
2. 仅在协议说明必要时使用绝对路径，且需同时标注对应相对路径。
3. 跨 Agent 上下文通过文档传递，不依赖会话记忆。
4. 架构/流程/资产变更后必须同步更新对应文档与 registry。
5. 未更新施工平面的推进不视为完成。

## 7. OpenClaw 操作基线（强制）

- 配置读取：`openclaw config get agents.list --json`
- 配置补丁：`openclaw gateway call config.patch --params '{"raw":"...","baseHash":"..."}' --json`
- 健康检查：`openclaw health --json`
- 会话检查：`openclaw sessions --json`
- 代理执行：`openclaw agent --message "..."`

### 7.1 工作区/Skill 源切换（M2+）

进入运行时开发/测试前必须执行：

- 开发模式：`python3 tools/openclaw/switch_workspace.py --repo-root <repo-or-worktree-root> --scope dev`
- 发布校验：`python3 tools/openclaw/switch_workspace.py --repo-root <repo-or-worktree-root> --scope public`

切换后最小校验（必须通过）：

- `openclaw config get agents.defaults.repoRoot --json`
- `openclaw config get skills.load.extraDirs --json`
- `openclaw skills info config-change-gatekeeper --json`（或本回合目标技能）

禁止把 `skills.entries.<key>.source` 直接写入 OpenClaw 运行配置。

### 7.2 长任务活性检测

1. 禁止使用固定时长到点即杀进程。
2. 先探活再判定卡死（输出流增量、会话活性、状态推进/心跳）。
3. 仅当连续无进展且证据支持时终止；默认观察窗口不少于 900 秒。
4. 终止必须落盘诊断证据并进入 HOLD/triage。

## 8. Entire 管理基线（Codex 强制）

1. 开始前检查：`entire status --detailed`，期望 `Enabled (manual-commit)`，否则执行 `entire enable --strategy manual-commit`。
2. 通过桥接启动：`python3 skills/system/entire-codex-sync/scripts/entire_codex_bridge.py start`
3. 每个有意义变更回合提交前执行：
   `python3 skills/system/entire-codex-sync/scripts/entire_codex_bridge.py sync --prompt "<需求>" --summary "<实现>" --files <changed-files...>`
4. 提交后校验：`git log -1 --pretty=raw`，提交信息必须包含 `Entire-Checkpoint: <id>`。
5. 任务结束关闭会话：`python3 skills/system/entire-codex-sync/scripts/entire_codex_bridge.py end`
6. 任一步失败或缺失 checkpoint，Fail-Closed，不得宣告完成。

协议文档：

- `docs/design/interfaces/entire-codex-sync-protocol.md`
- `skills/system/entire-codex-sync/references/bridge-contract.md`

## 9. Layer/Module 联动门禁（强制）

触发条件（任一满足）：

- 修改 `docs/design/layers/` 或 `docs/design/modules/` 的职责/边界/依赖/接口。
- 新增或重构 `skills/`、`processes/`、`agents/` 资产。

同回合必须同步：

- 设计文档：`docs/design/skills/`、`docs/design/processes/`、`docs/design/agents/`
- 清单：`docs/design/inventories/skill-inventory.md`、`docs/design/inventories/process-inventory.md`、`docs/design/inventories/agent-inventory.md`
- 注册表：`shared/registry/skill_registry.json`、`shared/registry/process_registry.json`、`shared/registry/agent_directory.json`
- 施工平面：`docs/architecture/construction_plane.md`

提交前最小校验：

- `python3 shared/registry/registry_contract_tool.py verify`
- `rg -n "<asset-id>" docs/design shared/registry`

任一联动缺失即未完成（Fail-Closed）。

## 10. 发布隔离与默认落盘（强制）

1. 运行数据默认落盘 `runtime_data/`。
2. 禁止将运行产物默认写入 `docs/design/modules/evidence/`、`agents/*/memory/` 等版本管理目录。
3. 标准发布资产仅允许 `agents/`、`skills/`、`processes/` 且进入 registry。
4. 私有/实验资产放在 `runtime_data/private-assets/{agents,skills,processes}/`，禁止进入 registry 与 OpenClaw 片段配置。

提交前最小校验：

- `git status --short`
- `python3 tools/release/generate_release_whitelist.py --strict`
- `python3 shared/registry/registry_contract_tool.py verify`
- `rg -n "runtime_data/private-assets" shared/registry config/openclaw.phase05*.fragment.json`
- `python3 tools/release/release_isolation_gate.py`
- 发布前追加：`python3 tools/release/release_isolation_gate.py --verify-openclaw`

标准打包命令：

- `python3 tools/release/build_release_bundle.py --verify-openclaw`
- 输出：`runtime_data/exports/release-bundles/<bundle-id>/`

---

## 11. 工作确认清单（DoD）

- [ ] 已阅读本文件与 SSOT。
- [ ] 本回合变更已同步文档、inventory、registry、施工平面。
- [ ] 必要 OpenClaw/Entire 校验已执行并留痕。
- [ ] 测试结论为自然语言且可支撑准入判断。
- [ ] 未触发任何 Fail-Closed 未闭环项。
