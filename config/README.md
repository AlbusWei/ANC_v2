# Config Fragments

## openclaw.phase05.fragment.json

用于 Phase 0.5 的 OpenClaw 配置基线片段：

1. `agents.list` 最小角色集（admin/architect/hr/kernel-dev/qa/bpm）。
2. `skills.entries` 对应 `skills/meta` 与 `processes/meta`。

## openclaw.phase05.with-entry.fragment.json

用于启用入口代理后的配置片段：

1. 在 `openclaw.phase05.fragment.json` 基础上追加 `personal-assistant` 到 `agents.list`。
2. 保持 `skills.entries` 与 Phase 0.5 基线一致。
3. 适用于需要默认入口代理的人机交互场景。

应用方式建议：

1. `openclaw gateway call config.get --params '{}' --json` 获取 `hash`。
2. 选择一个片段并合并成 JSON Merge Patch 的 `raw`（注意 `agents.list` 为数组字段，会整体覆盖）。
3. `openclaw gateway call config.patch --params '{"raw":"...","baseHash":"..."}' --json` 应用。
