# construction-plane-governance 流程设计

> 版本: v0.3.0 | 分类: Governance Process | 层级: P4 | owner: architect | 最后更新: 2026-02-21

## 目标

将 `M6` 施工面更新从“人工记忆驱动”升级为“流程驱动”，确保每次模块/层设计变化都完成联动文档、inventory、registry、施工平面与 OpenSpec 双向同步。

## 连续性与 phase 闭合

1. 本流程仅覆盖“施工治理连续段”，不跨生命周期非连续断点。
2. phase 映射闭合：
   - p1 映射 AP-001/AP-002/AP-003（需求摄取与范围基线）
   - p2 映射 AP-004（结构化审计产出）
   - p3 映射 AP-011（注册表与清单同步）
   - p4 映射 AP-011（OpenSpec 协同记录与同步状态校验）
   - p5 映射 AP-007 + AP-011（门禁验证与归档）
3. 若出现跨断点需求（如进入发布治理），必须由上级流程编排拆分，禁止在本流程内硬拼。

## 协同协议引用

1. OpenSpec 协同协议：`docs/design/interfaces/openspec-collaboration-protocol.md`
2. 执行策略：Phase 1 以文档级设计与阐释为主，运行级 dry-run 后置。

## 输入契约

1. `round_goal`
2. `change_scope_ref`
3. `changed_assets`
4. `linkage_targets`
5. `owner`
6. `openspec_ref`（架构相关变更必填）

## 输出契约

1. `m6_update_bundle_ref`
2. `linkage_report_ref`
3. `registry_verify_report_ref`
4. `construction_plane_delta_ref`
5. `open_questions_ref`
6. `openspec_sync_ref`

## 阶段定义

1. `p1 scope-intake-and-baseline`
   - actor: `bpm`
   - target: `system.ops.manual-task`
   - 目标：收敛回合目标、边界与影响面。
2. `p2 run-construction-audit`
   - actor: `architect`
   - target: `sys.arch.construction-audit`
   - 目标：输出联动缺口与阻断项清单。
3. `p3 execute-linked-updates`
   - actor: `architect`
   - target: `system.ops.manual-task`
   - 目标：补齐 design/inventory/registry/施工平面。
4. `p4 sync-openspec-state`
   - actor: `architect`
   - target: `system.integration.openspec-sync`
   - 目标：执行 OpenSpec 双向映射校验并产出结构化同步记录。
5. `p5 verify-and-close`
   - actor: `bpm`
   - target: `system.ops.manual-task`
   - 目标：执行契约校验、OpenSpec 同步校验并归档回合证据。

## 控制流

`p1 -> p2 -> p3 -> p4 -> p5 -> end`

## Fail-Closed

1. 联动目标缺失或不可追溯，直接阻断回合关闭。
2. `registry_contract_tool.py verify` 失败，禁止标记 Done。
3. 开放问题未记录 owner/下一步，禁止关闭回合。
4. 架构相关变更缺失 `openspec_ref` 或 `openspec_sync_ref`，禁止关闭回合。

## 证据包最小集

- `scope_baseline.md`
- `linkage_report.md`
- `update_delta.md`
- `registry_verify.log`
- `construction_plane_delta.md`
