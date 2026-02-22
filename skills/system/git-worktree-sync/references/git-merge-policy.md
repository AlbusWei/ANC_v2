# Git Worktree Merge Policy

## Scope

适用于同一仓库多 worktree 并行开发时的分支集成与扇出同步。

## Recommended Baseline

1. 明确角色
- `source`: 已完成阶段性修改的分支。
- `parent`: source 的母分支（例如 `rebuild`）。
- `siblings`: 其他并行 worktree 分支。

2. 统一入口
- 先做 `source -> parent`。
- parent 成功后，再做 `parent -> siblings`。

3. 同步前置
- 先 `git fetch <remote>`。
- parent 必须 `ff-only` 对齐远端。
- source/parent 工作区必须干净。

## Why This Is Safer

1. 避免把过时 parent 当作合并基线，减少反复冲突。
2. parent 先稳定，再扇出，防止兄弟分支各自对齐不同基线。
3. 对高改动兄弟分支直接 skip，减少“为了同步而同步”的冲突成本。

## Human-in-the-Loop Rules

1. 语义冲突由人类裁决
- 业务语义冲突、架构取舍冲突、删除/重命名冲突，必须人工决策。

2. AI 可自动处理范围
- 纯机械冲突（例如 import 排序、注释移动）且变更语义清晰时可自动解。
- 自动解后仍需执行最小回归测试。

## Disallowed Actions

1. 禁止将 `push --force` 作为常规同步路径。
2. 禁止在冲突处理中使用 `reset --hard` 覆盖未确认工作。
3. 禁止未跑最小验证就直接推送 parent。

## Suggested Thresholds for Sibling Auto-Sync

- `max_dirty_files`: 5
- `max_dirty_lines`: 200

超过阈值时默认 skip，等待该分支 owner 在合适时机手动同步。

## Optional Hardening

1. 打开 `rerere` 提升重复冲突复用：
- `git config rerere.enabled true`

2. 对 parent 开启受保护分支策略：
- 需要状态检查通过才允许推送/合并。

3. 将 `integrate` 与 `fanout` 结果写入统一日志，便于事后审计。
