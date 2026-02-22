---
name: "git-worktree-sync"
description: "Coordinate source->parent integration and parent->siblings fanout in multi-worktree Git repos with conflict-aware, fail-closed guardrails. Use when concurrent worktree branches must be merged and synchronized safely."
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.1.0"
---

# git-worktree-sync

## Objective

将多 worktree 并行开发中的分支同步流程固化为可执行、可回退、可审计的标准操作。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-phase1-worktree-branch-sync
input_contract:
  format: command_invocation
  required:
    - mode
    - parent_branch
  validation:
    - mode must be integrate or fanout
    - parent_branch must be a local branch and have remote tracking ref
    - integrate mode requires source_branch and source_branch != parent_branch
    - integrate mode requires clean source/parent worktrees
    - fanout mode only auto-merges siblings within dirty-change thresholds
output_contract:
  format: json_summary
  required:
    - mode
    - dry_run
    - results_or_steps
  machine_judgement:
    - all mutating commands are dry-run by default unless apply flag is set
    - parent branch is updated via ff-only before source merge
    - merge conflicts trigger abort and manual_required status
    - sibling branches with large WIP are skipped instead of forced merge
fail_closed_rules:
  - source or parent branch missing
  - parent branch cannot fast-forward to remote parent
  - merge conflict in integrate step
  - sibling merge conflict or stash-pop conflict
  - any attempt to force push or hard reset is disallowed
test_mount:
  test_doc: skills/system/git-worktree-sync/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  runner_script: skills/system/git-worktree-sync/scripts/worktree_sync.py
  policy_ref: skills/system/git-worktree-sync/references/git-merge-policy.md
```

## Runtime Rules

1. 默认 `dry-run`，只有显式 `--apply` 才允许改写分支。
2. 严格两阶段：先 `source -> parent`，再 `parent -> siblings`。
3. `parent` 更新必须 `ff-only`，禁止隐式 rebase 或历史改写。
4. 冲突默认 Fail-Closed：自动 `merge --abort`，转人工决策。
5. 对兄弟分支，WIP 过大必须 `skip`，而不是强行消冲突。
6. 禁止 `git push --force`、`git reset --hard` 作为常规路径。

## Execution Steps

1. 预演 source 合并到 parent：
   - `python3 skills/system/git-worktree-sync/scripts/worktree_sync.py integrate --source <source> --parent <parent>`
2. 执行 source 合并并推送 parent（可选跑测试）：
   - `python3 skills/system/git-worktree-sync/scripts/worktree_sync.py integrate --source <source> --parent <parent> --test-cmd "<tests>" --push --apply`
3. 预演 parent 扇出到兄弟分支：
   - `python3 skills/system/git-worktree-sync/scripts/worktree_sync.py fanout --parent <parent> --source <source> --max-dirty-files 5 --max-dirty-lines 200 --allow-dirty-stash`
4. 执行兄弟分支同步（按需 push）：
   - `python3 skills/system/git-worktree-sync/scripts/worktree_sync.py fanout --parent <parent> --source <source> --max-dirty-files 5 --max-dirty-lines 200 --allow-dirty-stash --apply`

## Conflict Escalation

- `integrate` 冲突：由人类决定冲突语义，解决后重跑 `integrate --apply`。
- `fanout` 冲突：单分支标记 `manual_conflict`，不阻塞其他兄弟分支继续同步。
- stash 回放冲突：标记人工处理，禁止脚本自动覆盖本地修改。

## Notes

- 推荐在 parent 合并成功后先跑最小回归再 push。
- 生产主干建议通过 PR 保护分支策略落地，本技能用于本地 worktree 编排和预处理。
