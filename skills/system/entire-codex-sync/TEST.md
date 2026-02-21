# entire-codex-sync - Test Cases

## Objective Alignment

验证 Codex 变更可被 Entire 生命周期桥接并写入提交 trailer 与会话证据。

## Test Cases

### TC-001: 回合同步后提交带 Checkpoint

- Type: Objective
- Priority: P0
- Input: `start -> sync --prompt/--summary/--files -> git commit`
- Expected: `git log -1 --pretty=raw` 含 `Entire-Checkpoint: <id>`
- Evaluation Method: Exact Match

### TC-002: Fail-Closed（Entire 未启用）

- Type: Objective
- Priority: P0
- Input: 在未启用 Entire 的仓库执行 `sync`
- Expected: 脚本返回非零并输出错误，不生成伪状态
- Evaluation Method: Exact Match

### TC-003: 状态可观测

- Type: Objective
- Priority: P1
- Input: 执行 `start/sync/end/status`
- Expected: `status` 输出会话 ID、active 状态、turns 和 transcript 路径
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
