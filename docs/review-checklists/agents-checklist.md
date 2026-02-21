# Agents Review Checklist

> Branch: `codex/review-agents`
> Worktree: `/Users/albus/MyProjects/ANC_v2_worktrees/review-agents`
> Baseline Commit: `d2d7699`

## 1. 目标

核对 Agent 角色设计、交接协议、inventory 与治理边界的一致性，确保角色可执行、可追溯、可审计。

## 2. SSOT 绑定

1. `/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/design/inventories/agent-inventory.md`
4. `/Users/albus/MyProjects/ANC_v2/docs/design/interfaces/role-handoff-protocol.md`
5. `/Users/albus/MyProjects/ANC_v2/docs/architecture/construction_plane.md`

## 3. 当前进度（d2d7699）

- [x] App 层角色文档已脱离 `_placeholder`，并纳入架构索引。
- [x] Role handoff 协议字段已与流程治理语义对齐。
- [x] agent inventory 与已落盘角色目录可对应。
- [ ] 新增角色的 runtime registry 生命周期推进（draft -> review）尚未完成。
- [ ] 角色协作的运行级证据（而非仅文档级）尚未完成。

## 4. 核对项

- [ ] 每个 Agent 文档包含：定位、输入输出、边界、Fail-Closed、升级链。
- [ ] Kernel/App/Control 角色职责无重叠且无空白区。
- [ ] `role-handoff-protocol.md` 与实际 Agent 文档字段一致。
- [ ] `agent-inventory.md`、`shared/registry/agent_directory.json`、文档目录三者一致。
- [ ] 架构文档中对 owner/admin/bpm 的治理描述与 Agent 定义一致。

## 5. 完成定义（DoD）

- [ ] 形成“阶段 -> Agent”覆盖矩阵并落盘。
- [ ] 至少 1 条跨角色交接链路有可回放证据。
- [ ] 变更仅包含 Agents 相关文档、inventory、必要 registry 同步。

## 6. 提交前校验

1. `entire status --detailed`
2. `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py sync --prompt "..." --summary "..." --files ...`
3. `python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify`
4. `git log -1 --pretty=raw`（确认 `Entire-Checkpoint`）
