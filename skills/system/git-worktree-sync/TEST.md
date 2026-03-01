# git-worktree-sync - Test Cases

## Objective Alignment

验证多 worktree 分支同步在冲突、脏工作区和远端漂移场景下保持 Fail-Closed。

## Test Cases

### TC-001: integrate 默认 dry-run

- Type: Objective
- Priority: P0
- Input: `integrate --source feature-a --parent rebuild`（不带 `--apply`）
- Expected: 输出 JSON 摘要，包含 `dry_run=true`，且不产生实际 merge/push
- Evaluation Method: Exact Match

### TC-002: integrate 冲突自动中止

- Type: Objective
- Priority: P0
- Input: `integrate --apply` 且 source 与 parent 存在冲突
- Expected: 返回 `manual_conflict`，触发 `merge --abort`，不继续 push
- Evaluation Method: Exact Match

### TC-003: fanout 跳过大规模 WIP 分支

- Type: Objective
- Priority: P0
- Input: `fanout --apply --max-dirty-files 5 --max-dirty-lines 200`，某兄弟分支超阈值
- Expected: 该分支标记 `skipped`，其他分支继续执行
- Evaluation Method: Exact Match

### TC-004: fanout 小规模脏修改允许 stash 合并

- Type: Objective
- Priority: P1
- Input: `fanout --apply --allow-dirty-stash`，兄弟分支脏改动在阈值内
- Expected: 先 stash，再 merge parent，最后 pop stash；成功时状态 `ok`
- Evaluation Method: Exact Match

### TC-005: stash 回放冲突 Fail-Closed

- Type: Objective
- Priority: P0
- Input: `fanout --apply --allow-dirty-stash`，stash pop 触发冲突
- Expected: 分支状态 `manual_conflict`，脚本不自动覆盖冲突内容
- Evaluation Method: Exact Match

### TC-006: 非默认 upstream 远端新鲜度

- Type: Objective
- Priority: P0
- Input: sibling 分支 upstream 指向非默认 remote，且该 remote 有新提交
- Expected: `fanout --apply` 后 sibling HEAD 包含最新 upstream 提交
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 900
- Retry Policy: max 1
