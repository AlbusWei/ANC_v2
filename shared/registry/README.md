# Registry

本目录存放 ANC v2 资产注册表：

1. `agent_directory.json`
2. `skill_registry.json`
3. `process_registry.json`

## 规则

1. 新增/修改/下线资产必须同步更新对应注册表。
2. registry 条目字段必须满足 `entry_contract.required`。
3. skill/process 条目必须与 `SKILL.md` frontmatter 对齐。

## 与 OpenClaw 映射

1. `skill_registry.entries[].name` 对应 OpenClaw `skills.entries[].name`。
2. `agent_directory.entries[].agent_id` 对应 OpenClaw `agents.list` 条目。
3. `process_registry.entries[].skill_name` 对应 process Skill 的 frontmatter `name`。

## 本地验证

```bash
jq . /Users/albus/MyProjects/ANC_v2/shared/registry/skill_registry.json
jq . /Users/albus/MyProjects/ANC_v2/shared/registry/process_registry.json
jq . /Users/albus/MyProjects/ANC_v2/shared/registry/agent_directory.json
```
