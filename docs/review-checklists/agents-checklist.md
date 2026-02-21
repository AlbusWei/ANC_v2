# Agents Review Checklist

> Branch: `codex/review-agents`
> Worktree: `/Users/albus/MyProjects/ANC_v2_worktrees/review-agents`

## 1. 目标

核对 agent 角色设计完整性、权限边界、协作与交接链路，确保 App/Kernal/Control 角色可治理。

## 2. Entire 执行要求（每次会话）

1. `entire status --detailed`
2. `.../entire_codex_bridge.py start`
3. 每回合改动后 `sync`
4. commit 后检查 `Entire-Checkpoint`
5. `.../entire_codex_bridge.py end`

## 3. 允许修改范围

1. `/Users/albus/MyProjects/ANC_v2/docs/design/agents/`
2. `/Users/albus/MyProjects/ANC_v2/docs/design/inventories/agent-inventory.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/review-checklists/agents-checklist.md`

## 4. 禁止修改范围

1. `/Users/albus/MyProjects/ANC_v2/docs/design/skills/`
2. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/`
3. `/Users/albus/MyProjects/ANC_v2/shared/registry/`

## 5. 核对项

1. 每个 agent 文档包含角色定位、绑定 skill、流程参与、边界、Fail-Closed。
2. architect/hr/system-analyst/app-analyst 职责边界不重叠且无空白区。
3. delivery 13 角色职责边界不重叠且无空白区。
4. evolution 3 角色（monitor/analyst/planner）职责闭环。
5. 协作模式文档与各 agent 文档一致。
6. owner/权限表述与治理逻辑不冲突。
7. `_placeholder` 迁移说明指向准确。
8. inventory 与 agent 文档清单一致。

## 6. 完成定义（DoD）

1. 所有 agent 文档满足统一结构。
2. 形成“角色覆盖矩阵”（阶段→负责角色）并可追溯。
3. 提交仅包含 agent、agent inventory 与本 checklist 文件。

## 7. 建议提交粒度

1. `agents: app role boundary refinement`
2. `agents: collaboration/inventory alignment`

## 8. 后续顺序改动清单（Post-Commit Follow-Ups）

1. Spec 标准化（Hybrid OpenSpec 字段映射）
   - Owner: architect
   - Trigger: 本轮角色边界落盘后立即启动
2. Objective 分层 Schema 补齐（OKR 树字段）
   - Owner: architect + qa
   - Trigger: Spec 标准化草案评审通过后
3. 流程角色同步（AP-001/AP-004/AP-015 与 handoff 契约）
   - Owner: bpm + architect
   - Trigger: Objective schema 字段冻结后
4. 模板治理协议化（双钥审批 `template_change_dual_approval_record`）
   - Owner: hr + architect
   - Trigger: 流程角色同步完成后
5. registry/interface 同步与审查用例
   - Owner: hr + bpm + qa
   - Trigger: 模板治理协议落盘后
