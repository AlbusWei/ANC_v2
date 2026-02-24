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

发布隔离策略配置：

`config/release.partition.json`

私有资产 overlay 示例：

`config/openclaw.private.overlay.example.json`

当前包含：

1. `phase05-base`：最小角色集（admin/architect/hr/kernel-dev/bpm/qa）。
2. `phase05-with-entry`：在 base 基础上加入 `personal-assistant`。

`release.partition.json` 用于声明公开发布与私有运行空间的边界（标准资产根目录、私有资产根目录、默认运行证据目录）。

`openclaw.private.overlay.example.json` 用于说明本地私有资产 overlay 的结构；真实私有 overlay 默认放在 `runtime_data/private-assets/openclaw.overlay.json`（不入库）。

发布白名单生成（严格）：

```bash
python3 tools/release/generate_release_whitelist.py --strict
```

标准发布打包（门禁 + 白名单 + 归档）：

```bash
python3 tools/release/build_release_bundle.py --verify-openclaw
```

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

1. 按 `--scope` 选择投影：
   - `public` -> `phase05-base`
   - `dev` -> `phase05-with-entry`
2. 先校验所选 profile 投影是否新鲜（Fail-Closed）。
3. 读取对应 fragment（或 `--fragment` 指定的片段）。
3. 将其中 repo-relative 的 `agents.list` 展开为目标仓库根目录下的绝对路径，并同步更新 `agents.defaults.repoRoot`、`tools.agentToAgent.allow`。
4. 将片段里的 `skills.entries.*.source` 展开为绝对路径，写入 `skills.load.extraDirs`（OpenClaw 2026.2 兼容写法）。
5. 若启用 `--enable-private-assets`：
   - 自动探测并附加存在的私有目录：`runtime_data/private-assets/processes`、`runtime_data/private-assets/skills`
   - 合并私有 overlay（默认 `runtime_data/private-assets/openclaw.overlay.json`）
6. 通过 `config.get + baseHash + config.patch` 原子写入。
7. 写入后回读校验：`agents.list`、`agents.defaults.repoRoot`、`skills.load.extraDirs`。

示例：

```bash
# 迁移到当前仓库目录
python3 tools/openclaw/switch_workspace.py --repo-root /Users/albus/MyProjects/ANC_v2 --scope dev

# 切换到某个 worktree
python3 tools/openclaw/switch_workspace.py \
  --repo-root /Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules \
  --scope dev

# 切到公开发布模式（不加载 app/entry 资产）
python3 tools/openclaw/switch_workspace.py \
  --repo-root /Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules \
  --scope public

# dev 模式 + 私有资产 overlay
python3 tools/openclaw/switch_workspace.py \
  --repo-root /Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules \
  --scope dev \
  --enable-private-assets \
  --private-overlay runtime_data/private-assets/openclaw.overlay.json

# 仅预览 patch（不写入）
python3 tools/openclaw/switch_workspace.py \
  --repo-root /Users/albus/MyProjects/ANC_v2 \
  --dry-run
```
