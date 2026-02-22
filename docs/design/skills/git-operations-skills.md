# Git Operations Skills 设计包

> 版本: v0.1.0 | 分类: System Skills | 最后更新: 2026-02-22

## 目标

定义多 worktree 并行开发场景下的 Git 分支集成与扇出同步能力，确保同步行为可执行、可审计、可回退。

关联文档：

1. `docs/design/standards/skill-definition-standard.md`
2. `skills/system/git-worktree-sync/SKILL.md`
3. `skills/system/git-worktree-sync/references/git-merge-policy.md`
4. `docs/architecture/construction_plane.md`

## 技能定义卡

### 1. system.ops.git-worktree-sync

- 定位：在多 worktree 并行开发中执行 `source -> parent` 集成与 `parent -> siblings` 扇出同步。
- owner：`admin`
- 输入契约：`mode`, `parent_branch`, `source_branch(when integrate)`, `siblings(optional)`, `dirty_thresholds`
- 输出契约：`mode`, `dry_run`, `steps/results`, `summary(manual_required count)`
- Fail-Closed：
  - branch 缺失或 parent 无法 `ff-only` 对齐远端 -> `fail`
  - merge 冲突或 stash 回放冲突 -> `manual_conflict`
  - 兄弟分支 WIP 超阈值 -> `skip`
  - 禁止 `force push`、`hard reset` 作为自动路径
- test_mount：`skills/system/git-worktree-sync/TEST.md`
- runner：`skills/system/git-worktree-sync/scripts/worktree_sync.py`
- 状态：`draft`

## 生命周期与落盘状态

1. `system.ops.git-worktree-sync` 已完成技能资产、测试文档、registry 与 inventory 对齐，当前保持 `draft`。
2. 进入 `review` 前置：
   - 在真实多 worktree 仓库上完成至少一轮 `integrate + fanout` 运行级验证。
   - `registry_contract_tool.py verify` 持续通过。
