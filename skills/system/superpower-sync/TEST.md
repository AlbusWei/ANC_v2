# superpower-sync - Test Cases

## Objective Alignment

验证 Superpower 同步包装技能可生成符合 schema 的同步记录，并在未初始化/校验失败时 Fail-Closed。

## Test Cases

### TC-001: 合法 Superpower 变更生成同步记录

- Type: Objective
- Priority: P0
- Input: 完整 `round_id + superpower_ref + anc_design_refs + decision_snapshot_ref + checkpoint_count + commit_count`
- Expected: 产出 `superpower_sync_ref` 且 `sync_status` 可解析
- Evaluation Method: Exact Match

### TC-002: Superpower 未初始化触发阻断

- Type: Objective
- Priority: P0
- Input: 在未执行 `superpower init` 的仓库调用
- Expected: Fail-Closed，返回 `blocked` 与错误原因
- Evaluation Method: Exact Match

### TC-003: strict validate 失败触发阻断

- Type: Objective
- Priority: P0
- Input: `superpower validate --strict` 返回失败
- Expected: Fail-Closed，输出 `validate_report_ref` 并阻断
- Evaluation Method: Exact Match

### TC-004: checkpoint 与 commit 计数不一致触发阻断

- Type: Objective
- Priority: P0
- Input: `checkpoint_count != commit_count`
- Expected: Fail-Closed，返回 `blocked`
- Evaluation Method: Exact Match
