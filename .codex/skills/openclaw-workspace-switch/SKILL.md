---
name: openclaw-workspace-switch
description: Switch OpenClaw runtime workspace between ANC_v2 main repo and worktrees with hash-safe patch + verification.
license: MIT
compatibility: Requires openclaw>=2026.2 and python3.
metadata:
  author: anc-v2
  version: "1.0.0"
---

切换 OpenClaw 运行时工作区（含 skills/processes 源目录）到目标仓库或 worktree。

## 适用场景

1. 从主仓切换到某个 worktree 做 M2+ 运行时开发/测试。
2. 从 worktree 切回主仓继续集成。
3. 运行前发现 `openclaw` 仍指向旧目录（如 `ANC` 而非 `ANC_v2`）。

## 执行步骤

1. 确认目标目录存在并且包含：
   - `config/openclaw.phase05.with-entry.fragment.json`
   - `shared/registry/registry_contract_tool.py`
2. 执行切换：
   - `python3 tools/openclaw/switch_workspace.py --repo-root <目标仓库或worktree根目录> --scope dev`
3. 执行最小校验：
   - `openclaw config get agents.defaults.repoRoot --json`
   - `openclaw config get agents.list --json`
   - `openclaw config get skills.load.extraDirs --json`
4. 可选运行时探针（建议）：
   - `openclaw skills info config-change-gatekeeper --json`
   - `openclaw agent --agent admin --message "请只回复你的当前workspace绝对路径。" --json`

## 常用命令

```bash
# 切到主仓
python3 tools/openclaw/switch_workspace.py --repo-root /Users/albus/MyProjects/ANC_v2 --scope dev

# 切到示例 worktree
python3 tools/openclaw/switch_workspace.py \
  --repo-root /Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules \
  --scope dev

# 切到公开发布模式（最小 agent 集）
python3 tools/openclaw/switch_workspace.py \
  --repo-root /Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules \
  --scope public

# dev 模式加载私有资产 overlay（若存在）
python3 tools/openclaw/switch_workspace.py \
  --repo-root /Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules \
  --scope dev \
  --enable-private-assets \
  --private-overlay runtime_data/private-assets/openclaw.overlay.json

# 只预览 patch
python3 tools/openclaw/switch_workspace.py \
  --repo-root /Users/albus/MyProjects/ANC_v2 \
  --dry-run
```

## 约束

1. 禁止手工写 `skills.entries.<key>.source`（OpenClaw 2026.2 会 `invalid config`）。
2. 仅允许通过 `tools/openclaw/switch_workspace.py` 切换（脚本内置 baseHash 并发保护与回读校验）。
3. 任一步失败即 Fail-Closed：停止后续运行时测试并先修复配置。
