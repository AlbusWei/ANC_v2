# Construction Plane Skills 设计包

> 版本: v0.3.0 | 分类: System Skills | 最后更新: 2026-02-21

## 目标

定义 `M6` 施工面治理能力的技能集合，确保 layer/module 联动门禁与 OpenSpec 协同同步可执行、可审计、可复盘。

关联规范：

1. `docs/design/modules/M6-construction-plane.md`
2. `docs/design/processes/construction-plane-governance-process.md`
3. `docs/architecture/construction_plane.md`
4. `docs/design/interfaces/openspec-collaboration-protocol.md`
5. `docs/design/data-models/openspec-collaboration-schema.json`

## 技能定义卡

### 1. sys.arch.construction-audit

- 定位：对单次变更回合执行“模块-技能-流程-注册表-施工平面”联动完整性审计。
- owner：`architect`
- 输入契约：`round_id`, `change_scope_ref`, `changed_assets`, `linkage_targets`, `round_goal`, `openspec_ref`
- 输出契约：`linkage_report_ref`, `missing_items`, `blocking_risks`, `recommended_actions`
- Fail-Closed：
  - 任一必填联动目标缺失 -> `fail`
  - 证据引用不可达 -> `fail`
  - OpenSpec 映射缺失或语义冲突未裁决 -> `fail`
  - 无法判定受影响边界 -> `hold`
- test_mount：`skills/system/construction-audit/TEST.md`
- AP 映射：`AP-033 construction-linkage-audit`
- 状态：`draft`（本轮新增并注册）

### 2. system.integration.openspec-sync

- 定位：调用本机 `openspec` CLI，输出符合完整 schema 的协同同步记录。
- owner：`architect`
- 输入契约：`round_id`, `round_goal`, `openspec_ref`, `anc_design_refs`, `decision_snapshot_ref`, `sync_actor`, `trigger_mode`, `risk_level`, `checkpoint_count`, `commit_count`, `round_evidence_log_ref`, `output_ref`
- 输出契约：`openspec_sync_ref`, `sync_status`, `validate_report_ref`, `status_report_ref`
- Fail-Closed：
  - OpenSpec CLI 不可用或仓库未初始化 -> `blocked`
  - strict validate 失败 -> `conflict`
  - 输出记录不满足 schema -> `blocked`
  - `checkpoint_count != commit_count` -> `blocked`
- test_mount：`skills/system/openspec-sync/TEST.md`
- AP 映射：`AP-035 openspec-round-sync`
- 状态：`draft`（本轮新增并注册）

## 生命周期与落盘状态

1. `sys.arch.construction-audit` 已落盘并进入 registry `draft`。
2. `system.integration.openspec-sync` 已落盘并进入 registry `draft`。
3. 进入 `review` 前置：
   - 至少一轮 M6 施工回合证据包
   - `registry_contract_tool.py verify` 连续通过
4. 进入 `active` 前置：
   - 模块改动联动门禁执行证据稳定（无漏项）
   - 与 `construction-plane-governance` 流程联动验证通过
