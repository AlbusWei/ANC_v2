# Config Fragments

## openclaw.phase05.fragment.json

用于 Phase 0.5 的 OpenClaw 配置基线片段：

1. `agents.list` 最小角色集（admin/architect/hr/kernel-dev/qa/bpm）。
2. `skills.entries` 对应 `skills/meta` 与 `processes/meta`。

应用方式建议：

1. `openclaw gateway call config.get --params '{}' --json` 获取 `hash`。
2. 将片段合并成 JSON Merge Patch 的 `raw`。
3. `openclaw gateway call config.patch --params '{"raw":"...","baseHash":"..."}' --json` 应用。
