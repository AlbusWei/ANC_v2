# construction-plane-governance 流程设计

> 版本: v0.7.0 | 分类: Governance Process | 层级: P4 | owner: architect | 最后更新: 2026-02-21

## 目标

将 `M6` 施工面更新从“人工记忆驱动”升级为“流程驱动”，确保每次模块/层设计变化都完成联动文档、inventory、registry、施工平面与 Superpower 双向同步。

## 连续性与 phase 闭合

1. 本流程仅覆盖“施工治理连续段”，不跨生命周期非连续断点。
2. phase 映射闭合：
   - p1 映射 AP-032（construction-round-intake-baseline）
   - p2 映射 AP-033（construction-linkage-audit）
   - p3 映射 AP-034（linked-artifacts-update）
   - p4 映射 AP-035（superpower-round-sync）
   - p5 映射 AP-036（construction-round-close-verification）
3. 若出现跨断点需求（如进入发布治理），必须由上级流程编排拆分，禁止在本流程内硬拼。

## 协同协议引用

1. Superpower 协同协议：`docs/design/interfaces/superpower-collaboration-protocol.md`
2. 执行策略：Phase 1 已完成运行级 dry-run（A/B/C），后续进入回归轮次。
3. 运行契约基线：`docs/design/processes/construction-plane-governance-runtime-contract-baseline.md`

## 输入契约

1. `round_id`
2. `round_goal`
3. `change_scope_ref`
4. `changed_assets`
5. `linkage_targets`
6. `owner`
7. `superpower_ref`（架构相关变更必填）

## 输出契约

1. `m6_update_bundle_ref`
2. `linkage_report_ref`
3. `registry_verify_report_ref`
4. `construction_plane_delta_ref`
5. `open_questions_ref`
6. `superpower_sync_ref`
7. `round_evidence_log_ref`
8. `round_close_summary_ref`

## 阶段定义

1. `p1 scope-intake-and-baseline`
   - actor: `bpm`
   - target: `system.ops.manual-task`
   - ap_ref: `docs/design/processes/atomic/AP-032-construction-round-intake-baseline.md`
   - 目标：收敛回合目标、边界与影响面。
2. `p2 run-construction-audit`
   - actor: `architect`
   - target: `sys.arch.construction-audit`
   - ap_ref: `docs/design/processes/atomic/AP-033-construction-linkage-audit.md`
   - 目标：输出联动缺口与阻断项清单。
3. `p3 execute-linked-updates`
   - actor: `architect`
   - target: `system.ops.manual-task`
   - ap_ref: `docs/design/processes/atomic/AP-034-linked-artifacts-update.md`
   - 目标：补齐 design/inventory/registry/施工平面。
4. `p4 sync-superpower-state`
   - actor: `architect`
   - target: `system.integration.superpower-sync`
   - ap_ref: `docs/design/processes/atomic/AP-035-superpower-round-sync.md`
   - 目标：执行 Superpower 双向映射校验并产出结构化同步记录。
   - 输入补充：`sync_actor`, `trigger_mode`, `risk_level`, `checkpoint_count`, `commit_count`, `output_ref`。
5. `p5 verify-and-close`
   - actor: `bpm`
   - target: `system.ops.manual-task`
   - ap_ref: `docs/design/processes/atomic/AP-036-construction-round-close-verification.md`
   - 目标：执行契约校验、Superpower 同步校验、checkpoint/commit 对账并归档回合证据。

## 控制流

`p1 -> p2 -> p3 -> p4 -> p5 -> end`

## Runtime Tooling

1. `processes/meta/construction-plane-governance/scripts/run_round.py`
2. `processes/meta/construction-plane-governance/scripts/round_evidence_tool.py`

## Fail-Closed

1. 联动目标缺失或不可追溯，直接阻断回合关闭。
2. `registry_contract_tool.py verify` 失败，禁止标记 Done。
3. `registry_contract_tool.py verify-m6 --round-dir <round-dir>` 失败，禁止标记 Done。
4. 开放问题未记录 owner/下一步，禁止关闭回合。
5. 架构相关变更缺失 `superpower_ref` 或 `superpower_sync_ref`，禁止关闭回合。
6. 任一代码提交缺失 `Entire-Checkpoint`，禁止关闭回合。
7. `checkpoint_count` 与 `commit_count` 不一致，禁止关闭回合。
8. 同一 `round_id` 出现多个 `superpower_ref`，禁止关闭回合。
9. 回合日志缺失 `round_close` 事件，禁止关闭回合。

## 证据包最小集

- `scope_baseline.md`
- `linkage_report.md`
- `update_delta.md`
- `registry_verify.log`
- `construction_plane_delta.md`
- `round-evidence.jsonl`
- `round-close-summary.md`

<!-- phase-semantics-v2:start -->
## 阶段协作语义补充（v2）

> 说明：本节用于说明每个 phase 在系统主线中的职责与协作价值，要求可直接回答“为什么由该 Actor 在该阶段执行该动作”。

| phase_id | Actor | 阶段目的 | 输入语义 | 完成标准 | 交接语义 |
|---|---|---|---|---|---|
| `p1` | `bpm` | 设定本轮治理的范围与边界基线。 | round_id + round_goal + change_scope_ref + changed_assets + linkage_targets + superpower_ref | 产出 scope_baseline_ref，并满足：范围基线包含模块边界与联动目标 | 将 scope_baseline_ref 交接给 p2 |
| `p2` | `architect` | 审计联动项完整性并识别阻塞缺口。 | round_id + scope_baseline_ref + linkage_targets + changed_assets + superpower_ref | 产出 linkage_report_ref，并满足：联动报告包含缺项与阻塞风险 | 将 linkage_report_ref 交接给 p3 |
| `p3` | `architect` | 在设计文档、清单与注册表中同步落盘联动更新。 | round_id + linkage_report_ref + changed_assets | 产出 m6_update_bundle_ref + construction_plane_delta_ref + open_questions_ref，并满足：所有必需联动资产在同一轮次完成更新 | 将 m6_update_bundle_ref + construction_plane_delta_ref + open_questions_ref 交接给 p4 |
| `p4` | `architect` | 执行 Superpower 同步并生成机器可读记录。 | round_id + round_goal + superpower_ref + anc_design_refs + decision_snapshot_ref + sync_actor + trigger_mode + risk_level + checkpoint_count + commit_count + round_evidence_log_ref + output_ref | 产出 superpower_sync_ref，并满足：Superpower 同步记录已生成且符合 schema | 将 superpower_sync_ref 交接给 p5 |
| `p5` | `bpm` | 执行 registry 校验并完成 checkpoint 与开放问题对账后收口本轮。 | round_id + m6_update_bundle_ref + superpower_sync_ref + round_evidence_log_ref + open_questions_ref | 产出 registry_verify_report_ref + round_close_summary_ref + construction_plane_delta_ref + open_questions_ref，并满足：registry 校验通过且开放问题已落实负责人 | 将 registry_verify_report_ref + round_close_summary_ref + construction_plane_delta_ref + open_questions_ref 交接给 initiator |
<!-- phase-semantics-v2:end -->
