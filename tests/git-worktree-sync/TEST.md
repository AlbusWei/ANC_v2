# git-worktree-sync - Runtime Validation Test Cases

## Objective Alignment

验证 `system.ops.git-worktree-sync` 在多 worktree + 多远端并发场景下满足 Fail-Closed、冲突回退与同步新鲜度要求。

## Test Cases

### TC-001: integrate dry-run 仅输出计划

- Type: Objective
- Priority: P0
- Input: clean source/parent worktree + `integrate`（无 `--apply`）
- Expected: 返回 `mode=integrate`、`dry_run=true`、`result=ok`
- Evaluation Method: Exact Match

### TC-002: fanout 对超阈值脏分支执行 skip

- Type: Objective
- Priority: P0
- Input: sibling dirty changes 超过阈值，未启用 `--allow-dirty-stash`
- Expected: sibling 状态 `skipped`，不执行 merge
- Evaluation Method: Rule Match

### TC-003: fanout 冲突时 Fail-Closed

- Type: Objective
- Priority: P0
- Input: sibling 与 parent 对同一行冲突，执行 `fanout --apply`
- Expected: sibling 状态 `manual_conflict` 且 merge 已 `--abort`
- Evaluation Method: Exact Match

### TC-004: fanout 非默认 upstream 远端新鲜度

- Type: Objective
- Priority: P0
- Input: sibling upstream 指向非默认 remote（如 `mirror/*`），远端有新提交
- Expected: 同步后 sibling HEAD 必须包含最新 upstream 提交
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 900
- Retry Policy: max 1
