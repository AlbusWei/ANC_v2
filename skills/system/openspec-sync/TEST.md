# openspec-sync - Test Cases

## Objective Alignment

验证 OpenSpec 同步包装技能可生成符合 schema 的同步记录，并在未初始化/校验失败时 Fail-Closed。

## Test Cases

### TC-001: 合法 OpenSpec 变更生成同步记录

- Type: Objective
- Priority: P0
- Input: 完整 `openspec_ref + anc_design_refs + decision_snapshot_ref`
- Expected: 产出 `openspec_sync_ref` 且 `sync_status` 可解析
- Evaluation Method: Exact Match

### TC-002: OpenSpec 未初始化触发阻断

- Type: Objective
- Priority: P0
- Input: 在未执行 `openspec init` 的仓库调用
- Expected: Fail-Closed，返回 `blocked` 与错误原因
- Evaluation Method: Exact Match

### TC-003: strict validate 失败触发阻断

- Type: Objective
- Priority: P0
- Input: `openspec validate --strict` 返回失败
- Expected: Fail-Closed，输出 `validate_report_ref` 并阻断
- Evaluation Method: Exact Match
