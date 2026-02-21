# construction-plane-governance 流程设计

> 版本: v0.5.0 | 分类: Governance Process | 层级: P4 | owner: architect | 最后更新: 2026-02-21

## 目标

将 `M6` 施工面更新从“人工记忆驱动”升级为“流程驱动”，确保每次模块/层设计变化都完成联动文档、inventory、registry、施工平面与 OpenSpec 双向同步。

## 连续性与 phase 闭合

1. 本流程仅覆盖“施工治理连续段”，不跨生命周期非连续断点。
2. phase 映射闭合：
   - p1 映射 AP-032（construction-round-intake-baseline）
   - p2 映射 AP-033（construction-linkage-audit）
   - p3 映射 AP-034（linked-artifacts-update）
   - p4 映射 AP-035（openspec-round-sync）
   - p5 映射 AP-036（construction-round-close-verification）
3. 若出现跨断点需求（如进入发布治理），必须由上级流程编排拆分，禁止在本流程内硬拼。

## 协同协议引用

1. OpenSpec 协同协议：`docs/design/interfaces/openspec-collaboration-protocol.md`
2. 执行策略：Phase 1 以文档级设计与阐释为主，运行级 dry-run 后置。

## 输入契约

1. `round_id`
2. `round_goal`
3. `change_scope_ref`
4. `changed_assets`
5. `linkage_targets`
6. `owner`
7. `openspec_ref`（架构相关变更必填）

## 输出契约

1. `m6_update_bundle_ref`
2. `linkage_report_ref`
3. `registry_verify_report_ref`
4. `construction_plane_delta_ref`
5. `open_questions_ref`
6. `openspec_sync_ref`
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
4. `p4 sync-openspec-state`
   - actor: `architect`
   - target: `system.integration.openspec-sync`
   - ap_ref: `docs/design/processes/atomic/AP-035-openspec-round-sync.md`
   - 目标：执行 OpenSpec 双向映射校验并产出结构化同步记录。
5. `p5 verify-and-close`
   - actor: `bpm`
   - target: `system.ops.manual-task`
   - ap_ref: `docs/design/processes/atomic/AP-036-construction-round-close-verification.md`
   - 目标：执行契约校验、OpenSpec 同步校验、checkpoint/commit 对账并归档回合证据。

## 控制流

`p1 -> p2 -> p3 -> p4 -> p5 -> end`

## Fail-Closed

1. 联动目标缺失或不可追溯，直接阻断回合关闭。
2. `registry_contract_tool.py verify` 失败，禁止标记 Done。
3. 开放问题未记录 owner/下一步，禁止关闭回合。
4. 架构相关变更缺失 `openspec_ref` 或 `openspec_sync_ref`，禁止关闭回合。
5. 任一代码提交缺失 `Entire-Checkpoint`，禁止关闭回合。
6. `checkpoint_count` 与 `commit_count` 不一致，禁止关闭回合。
7. 同一 `round_id` 出现多个 `openspec_ref`，禁止关闭回合。
8. 回合日志缺失 `round_close` 事件，禁止关闭回合。

## 证据包最小集

- `scope_baseline.md`
- `linkage_report.md`
- `update_delta.md`
- `registry_verify.log`
- `construction_plane_delta.md`
- `round-evidence.jsonl`
- `round-close-summary.md`
