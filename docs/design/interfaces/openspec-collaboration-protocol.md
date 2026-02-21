# OpenSpec 协同协议（Hybrid）

> 版本: v0.3.0 | 状态: draft | 最后更新: 2026-02-21

## 1. 目标

定义 ANC 本地设计文档与 OpenSpec 的协同边界与同步规则，避免双系统语义分歧和重复维护。

## 2. Hybrid 原则

1. ANC 文档是治理契约与落盘真相源（SSOT for governance contracts）。
2. OpenSpec 是协同评审与提案工作台（workspace for collaboration）。
3. 双向引用、单点裁决：
   - 双向引用：两侧都必须保留对侧锚点。
   - 单点裁决：冲突由 `architect` 在 ANC 文档中裁决并回写 OpenSpec。

## 3. 角色分工

1. `architect`：M6 语义 owner，负责冲突裁决与最终语义收敛。
2. `bpm`：执行同步动作与证据归档，确保回合可追溯。
3. `system-analyst`：提供变更密度与风险信号，触发可调频巡检建议。
4. `admin`：仅在跨系统配置/权限问题时介入，不直接裁决语义。

## 4. 最小映射字段

每个架构相关施工回合至少落盘以下字段：

1. `round_id`：施工回合唯一标识。
2. `openspec_ref`：OpenSpec 变更线程或提案引用。
3. `anc_design_refs`：受影响 ANC 设计文档路径列表。
4. `decision_snapshot_ref`：architect 裁决快照。
5. `sync_status`：`in_sync|needs_sync|conflict`。
6. `sync_timestamp`。

## 4.1 回合绑定规则（强制）

1. 固定映射：`1 round = 1 OpenSpec change = N Entire checkpoints = N git commits`。
2. 同一 `round_id` 下，`openspec_ref` 必须保持单值一致。
3. 每个 `entire_checkpoint_id` 仅允许归属一个 `round_id`，禁止跨回合复用。
4. `construction_plane.md` 主文档只在回合关闭时写入汇总；提交级证据写入回合 JSONL 日志。

## 4.2 round_id 规范（强制）

1. 格式：`R-YYYYMMDD-M6-<change_key>-NN`。
2. 正则：`^R-\d{8}-M6-[a-z0-9-]+-\d{2}$`。
3. `change_key` 从 `openspec_ref` 派生稳定短键。
4. `NN` 序号按同一 `change_key` 递增。

## 4.3 完整 Schema（强制）

1. 机器可读 Schema 固定为：`docs/design/data-models/openspec-collaboration-schema.json`。
2. 施工回合若包含 OpenSpec 协同，输出记录必须完整满足该 Schema，禁止“仅部分字段约定”。
3. `sync_status` 统一枚举：`in_sync|needs_sync|conflict|blocked`。
4. `trigger_mode` 统一枚举：`change_triggered|analyst_inspection`。
5. `inspection_profile`、`conflict_state`、`evidence_bundle`、`sync_actions` 均为必填结构化对象。

## 5. 同步触发规则

1. 变更触发：当 layer/module 设计职责、边界、依赖发生变化时，必须触发同步。
2. 巡检触发：`system-analyst` 根据风险与变更密度触发巡检，不固定周频，支持日级高频到周级低频的动态调频。
3. 关闭触发：施工回合关闭前必须完成双向映射校验。

## 6. 冲突与 Fail-Closed

1. OpenSpec 与 ANC 语义冲突且无裁决快照 -> `conflict`，禁止关闭回合。
2. 架构相关回合缺失 `openspec_ref` -> `needs_sync`，禁止标记 Done。
3. 仅更新任一侧而未回填另一侧 -> `needs_sync`，禁止进入下一里程碑。
4. 同步记录不满足完整 Schema -> `blocked`，禁止关闭回合。

## 7. 证据包最小集

- `openspec_linkage.json`
- `anc_delta_index.json`
- `decision_snapshot.md`
- `sync_check_report.md`
- `round-evidence.jsonl`

### 7.1 round-evidence.jsonl 事件模型

1. 事件类型：`round_open`、`checkpoint_synced`、`round_close`。
2. `round_open` 必填：`round_id`、`openspec_ref`、`round_goal`、`owner`、`ts`。
3. `checkpoint_synced` 必填：`round_id`、`openspec_ref`、`entire_checkpoint_id`、`commit_sha`、`changed_files`、`sync_status`、`ts`。
4. `round_close` 必填：`round_id`、`openspec_ref`、`decision_snapshot_ref`、`final_sync_status`、`checkpoint_count`、`commit_count`、`verdict`、`ts`。
5. `round_open` 必须唯一且先于其他事件；`round_close` 必须唯一且位于日志末尾。

## 8. 与 M6 的咬合

1. `M6` 输出包必须包含 `openspec_sync_ref`。
2. `construction-plane-governance` 流程在 `verify-and-close` 阶段执行 OpenSpec 同步校验。
3. `construction_plane.md` 的开放问题与决策状态需与 OpenSpec 线程状态一致，并在回合关闭时写入摘要。
4. `registry_contract_tool.py verify` 必须包含 OpenSpec 协同 Schema 一致性校验。
5. 提交建议携带 `Entire-Checkpoint`、`Round-ID`、`OpenSpec-Change` 三类 trailer，用于回合审计与对账。

## 9. 扩展 Fail-Closed（回合对账）

1. 回合内任一代码提交缺失 `Entire-Checkpoint` -> 禁止关闭回合。
2. `checkpoint_count != commit_count` -> 判定 `blocked` 并禁止关闭回合。
3. 同一 `round_id` 关联多个 `openspec_ref` -> 判定 `conflict` 并禁止关闭回合。
