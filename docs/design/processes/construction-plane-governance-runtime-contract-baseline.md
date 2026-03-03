# construction-plane-governance Runtime Contract Baseline

> 版本: v0.1.0 | 状态: draft | 最后更新: 2026-02-21

## 目标

冻结 `construction-plane-governance` 在运行时的输入/输出契约与 AP-032~AP-036 映射字段，作为 M6 CLI 执行器与门禁校验的唯一基线。

## 回合输入包（P4 process input_contract）

必填字段：

1. `round_id`
2. `round_goal`
3. `change_scope_ref`
4. `changed_assets`
5. `linkage_targets`
6. `owner`
7. `superpower_ref`

## 回合输出包（P4 process output_contract）

必填字段：

1. `m6_update_bundle_ref`
2. `linkage_report_ref`
3. `superpower_sync_ref`
4. `registry_verify_report_ref`
5. `construction_plane_delta_ref`
6. `open_questions_ref`
7. `round_evidence_log_ref`
8. `round_close_summary_ref`

## Phase/AP 映射与字段冻结

1. `p1 -> AP-032`
   - 输入：`round_id`, `round_goal`, `change_scope_ref`, `changed_assets`, `linkage_targets`, `owner`, `superpower_ref`
   - 输出：`scope_baseline_ref`
2. `p2 -> AP-033`
   - 输入：`round_id`, `scope_baseline_ref`, `linkage_targets`, `changed_assets`, `superpower_ref`
   - 输出：`linkage_report_ref`, `missing_items`, `blocking_risks`, `recommended_actions`
3. `p3 -> AP-034`
   - 输入：`round_id`, `linkage_report_ref`, `changed_assets`
   - 输出：`m6_update_bundle_ref`, `construction_plane_delta_ref`, `open_questions_ref`
4. `p4 -> AP-035`
   - 输入：`round_id`, `round_goal`, `superpower_ref`, `anc_design_refs`, `decision_snapshot_ref`, `sync_actor`, `trigger_mode`, `risk_level`, `checkpoint_count`, `commit_count`, `round_evidence_log_ref`, `output_ref`
   - 输出：`superpower_sync_ref`, `sync_status`, `validate_report_ref`, `status_report_ref`
5. `p5 -> AP-036`
   - 输入：`round_id`, `m6_update_bundle_ref`, `superpower_sync_ref`, `round_evidence_log_ref`, `open_questions_ref`
   - 输出：`registry_verify_report_ref`, `round_close_summary_ref`

## Fail-Closed 对账规则

1. `round_id` 必须匹配 `^R-\d{8}-M6-[a-z0-9-]+-\d{2}$`。
2. 回合日志事件只允许 `round_open`、`checkpoint_synced`、`round_close`。
3. `round_open` 必须唯一且位于首行。
4. `round_close` 必须唯一且位于末行。
5. 单个 `round_id` 只能绑定单个 `superpower_ref`。
6. `checkpoint_count == commit_count`。
7. 若提供 `--git-range`，范围内每个 commit 必须包含 `Entire-Checkpoint` trailer。
8. 缺 `round_close_summary_ref` 禁止判定 Done。

## 样例 payload

样例文件：`docs/design/processes/samples/construction-plane-governance/m6-runtime-contract-examples.json`

