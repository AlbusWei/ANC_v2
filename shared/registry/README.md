# Registry

本目录存放 ANC v2 资产注册表：

1. `agent_directory.json`
2. `skill_registry.json`
3. `process_registry.json`
4. `registry_contract_tool.py`

## 规则

1. 新增/修改/下线资产必须同步更新对应注册表。
2. `entry_contract` 是机器真相源，字段校验以 `entry_contract.properties` 为准。
3. `entry_contract.additionalProperties` 必须为 `false`（Fail-Closed）。
4. skill/process 条目必须与 `SKILL.md` frontmatter 对齐。

## 与 OpenClaw 映射

1. `agent_directory.entries[]` 投影到 OpenClaw `agents.list`。
2. `skill_registry` / `process_registry` 投影到 OpenClaw `skills.entries`。
3. pin 条目使用稳定键：`skill_id` / `process_id`。
4. bundle + pin 同时命中时，pin 优先。

## 本地验证

```bash
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py validate
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py generate-docs --check
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py project-openclaw --all --check
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify
```
