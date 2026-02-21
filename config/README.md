# Config Fragments

## 管理方式

`openclaw.phase05.fragment.json` 与 `openclaw.phase05.with-entry.fragment.json` 的受管区由
`/Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py`
根据 registry 自动投影生成。

受管区仅包含：

1. `agents.list`
2. `skills.entries`

非受管区（如 `channels`、`channelsConfig`）由 admin/BPM 按治理流程维护，工具不会覆盖。

## Projection Profiles

profile 定义文件：

`/Users/albus/MyProjects/ANC_v2/config/openclaw.projection.profiles.json`

当前包含：

1. `phase05-base`：最小角色集（admin/architect/hr/kernel-dev/bpm/qa）。
2. `phase05-with-entry`：在 base 基础上加入 `personal-assistant`。

## 生成与校验命令

```bash
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py project-openclaw --all
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py project-openclaw --all --check
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify
```

## 应用方式建议

1. `openclaw gateway call config.get --params '{}' --json` 获取 `hash`。
2. 选择目标片段并构建 JSON Merge Patch 的 `raw`（`agents.list` 是数组字段，会整体覆盖）。
3. `openclaw gateway call config.patch --params '{"raw":"...","baseHash":"..."}' --json` 应用。
