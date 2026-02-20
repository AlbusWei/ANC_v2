# 注册表 Schema 详细定义

> 版本: v0.1.0 | SSOT 上游: [registry_contracts.md](../../architecture/registry_contracts.md)

## agent_directory.json Schema

```json
{
  "agents": [{
    "agent_id": "string (kebab-case, required, unique)",
    "layer": "string (kernel|control|app, required)",
    "path": "string (相对项目根的目录路径, required)",
    "default_model": "string (LLM 模型标识, required)",
    "owner": "string (agent_id|'human', required)",
    "status": "string (draft|review|active|deprecated|retired, required)",
    "bindings": {
      "channels": ["string (OpenClaw channel 名)"],
      "channelsConfig": {}
    },
    "permissions": ["string (权限标识)"],
    "skills": ["string (skill_id 引用)"]
  }]
}
```

### 字段约束

| 字段 | 类型 | 约束 |
|---|---|---|
| agent_id | string | kebab-case, 全局唯一 |
| layer | enum | kernel, control, app |
| path | string | 目录必须存在，包含 7 文件模板 |
| owner | string | 必须是已注册 agent_id 或 "human" |
| status | enum | 遵循统一生命周期状态机 |

## skill_registry.json Schema

```json
{
  "skills": [{
    "skill_id": "string (dot-notation, required, unique)",
    "name": "string (kebab-case, required)",
    "path": "string (SKILL.md 所在目录, required)",
    "layer": "string (meta|system|business, required)",
    "owner": "string (agent_id, required)",
    "version": "string (semver, required)",
    "status": "string (draft|review|active|deprecated|retired, required)",
    "agentskills": {
      "name": "string (与 SKILL.md frontmatter 一致)",
      "description": "string",
      "license": "string",
      "compatibility": "string"
    },
    "openclaw": {
      "entry_name": "string (skills.entries[].name)",
      "install_strategy": "string (lazy|eager)"
    },
    "tests": {
      "test_doc": "string (TEST.md 路径)",
      "methodology_ref": "string"
    }
  }]
}
```

## process_registry.json Schema

```json
{
  "processes": [{
    "process_id": "string (kebab-case, required, unique)",
    "skill_name": "string (OpenClaw skill 名, required)",
    "skill_path": "string (SKILL.md 所在目录, required)",
    "manifest_path": "string (process.json 路径, required)",
    "objective_ref": "string (Objective 引用)",
    "owner": "string (agent_id, required)",
    "version": "string (semver, required)",
    "status": "string (draft|review|active|deprecated|retired, required)",
    "phase_count": "integer (阶段数, required)",
    "openclaw": {
      "entry_name": "string",
      "install_strategy": "string"
    }
  }]
}
```

## 校验规则

1. **JSON 语法**: 所有 registry 文件必须是合法 JSON
2. **路径存在性**: path/skill_path/manifest_path 指向的文件/目录必须存在
3. **名称一致性**: skill_registry 的 name 必须与 SKILL.md frontmatter name 一致
4. **版本一致性**: registry version 必须与资产文件中声明的版本一致
5. **唯一性**: agent_id/skill_id/process_id 全局唯一
6. **引用完整性**: owner 必须是已注册的 agent_id
