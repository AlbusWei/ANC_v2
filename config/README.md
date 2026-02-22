# Config Fragments

## 管理方式

`openclaw.phase05.fragment.json` 与 `openclaw.phase05.with-entry.fragment.json` 的受管区由
`shared/registry/registry_contract_tool.py`
根据 registry 自动投影生成。

受管区仅包含：

1. `agents.list`
2. `skills.entries`

非受管区（如 `channels`、`channelsConfig`）由 admin/BPM 按治理流程维护，工具不会覆盖。

## Projection Profiles

profile 定义文件：

`config/openclaw.projection.profiles.json`

当前包含：

1. `phase05-base`：最小角色集（admin/architect/hr/kernel-dev/bpm/qa）。
2. `phase05-with-entry`：在 base 基础上加入 `personal-assistant`。

## 生成与校验命令

```bash
python3 shared/registry/registry_contract_tool.py project-openclaw --all
python3 shared/registry/registry_contract_tool.py project-openclaw --all --check
python3 shared/registry/registry_contract_tool.py verify
```

## 应用方式建议

1. `openclaw gateway call config.get --params '{}' --json` 获取 `hash`。
2. 选择目标片段并构建 JSON Merge Patch 的 `raw`（`agents.list` 是数组字段，会整体覆盖）。
3. `openclaw gateway call config.patch --params '{"raw":"...","baseHash":"..."}' --json` 应用。

## 工作区迁移与 Worktree 切换

为避免手工拼接 patch，使用脚本：

`tools/openclaw/switch_workspace.py`

行为：

1. 先校验 `phase05-with-entry` 投影是否新鲜（Fail-Closed）。
2. 读取 `config/openclaw.phase05.with-entry.fragment.json`。
3. 将其中 repo-relative 的 `agents.list` 展开为目标仓库根目录下的绝对路径，并同步更新 `agents.defaults.repoRoot`、`tools.agentToAgent.allow`。
4. 将片段里的 `skills.entries.*.source` 展开为绝对路径，写入 `skills.load.extraDirs`（OpenClaw 2026.2 兼容写法）。
5. 通过 `config.get + baseHash + config.patch` 原子写入。
6. 写入后回读校验：`agents.list`、`agents.defaults.repoRoot`、`skills.load.extraDirs`。

示例：

```bash
# 迁移到当前仓库目录
python3 tools/openclaw/switch_workspace.py --repo-root /Users/albus/MyProjects/ANC_v2

# 切换到某个 worktree
python3 tools/openclaw/switch_workspace.py \
  --repo-root /Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules

# 仅预览 patch（不写入）
python3 tools/openclaw/switch_workspace.py \
  --repo-root /Users/albus/MyProjects/ANC_v2 \
  --dry-run
```
