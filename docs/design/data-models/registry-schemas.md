# 注册表 Schema 详细定义

> 本文档由 `/Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py` 自动生成。
> 机器真相源：`shared/registry/*_registry.json` 中的 `entry_contract`。

## agent_directory.json

- schema_version: `1.1.0`
- updated_at: `2026-02-21T18:00:00Z`
- strict mode: `true`

| 字段 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| `agent_id` | `string` | `true` | `pattern=^[a-z0-9-]+$` | stable agent identifier |
| `layer` | `string` | `true` | `enum=kernel,control,app` | layer classification |
| `path` | `string` | `true` | `pattern=^/Users/albus/MyProjects/ANC_v2/.+` | absolute agent workspace path |
| `default_model` | `string` | `true` | `` | default llm model |
| `owner` | `string` | `true` | `` | owner agent_id or human |
| `status` | `string` | `true` | `enum=draft,review,active,deprecated,retired` | lifecycle status |
| `permissions` | `array<string>` | `true` | `minItems=1; uniqueItems=true` | permission scopes |
| `bindings` | `object` | `true` | `` | openclaw channel bindings |
| `bindings.channels` | `array<string>` | `true` | `uniqueItems=true` | referenced channel names |
| `bindings.channelsConfig` | `object` | `true` | `` | channel-level agent config |

示例条目：

```json
{
  "agent_id": "admin",
  "layer": "kernel",
  "path": "/Users/albus/MyProjects/ANC_v2/agents/kernel/admin",
  "default_model": "rightcode/gpt-5.3-codex",
  "owner": "human",
  "status": "draft",
  "permissions": [
    "system-root"
  ],
  "bindings": {
    "channels": [],
    "channelsConfig": {}
  }
}
```

## skill_registry.json

- schema_version: `1.1.0`
- updated_at: `2026-02-21T18:00:00Z`
- strict mode: `true`

| 字段 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| `skill_id` | `string` | `true` | `pattern=^[a-z0-9]+(\.[a-z0-9-]+)+$` | stable skill identifier |
| `name` | `string` | `true` | `pattern=^[a-z0-9-]+$` | skill display name |
| `path` | `string` | `true` | `pattern=^/Users/albus/MyProjects/ANC_v2/.+` | absolute SKILL.md path |
| `layer` | `string` | `true` | `enum=meta,system,business` | skill layer |
| `owner` | `string` | `true` | `` | owner agent_id |
| `version` | `string` | `true` | `pattern=^[0-9]+\.[0-9]+\.[0-9]+$` | semantic version |
| `status` | `string` | `true` | `enum=draft,review,active,deprecated,retired` | lifecycle status |
| `agentskills` | `object` | `true` | `` | agent skills frontmatter snapshot |
| `agentskills.name` | `string` | `true` | `` | frontmatter name |
| `agentskills.description` | `string` | `true` | `` | frontmatter description |
| `agentskills.license` | `string` | `true` | `` | frontmatter license |
| `agentskills.compatibility` | `object` | `true` | `` | compatibility matrix |
| `agentskills.compatibility.openclaw` | `string` | `true` | `` | openclaw compatibility range |
| `agentskills.compatibility.agentskills` | `string` | `true` | `` | agentskills compatibility range |
| `openclaw` | `object` | `true` | `` | OpenClaw projection metadata |
| `openclaw.projection_mode` | `string` | `true` | `enum=bundle,pin,off` | projection strategy |
| `openclaw.entry_key` | `string` | `true` | `` | stable OpenClaw entry key |
| `openclaw.source` | `string` | `true` | `pattern=^/Users/albus/MyProjects/ANC_v2/.+` | OpenClaw source path |
| `openclaw.install_strategy` | `string` | `true` | `enum=lazy,eager` | OpenClaw install strategy |
| `openclaw.bundle_key` | `string` | `false` | `` | bundle key when projection_mode=bundle |
| `openclaw.bundle_source` | `string` | `false` | `pattern=^/Users/albus/MyProjects/ANC_v2/.+` | bundle source when projection_mode=bundle |
| `openclaw.allow_draft_projection` | `boolean` | `false` | `` | allow draft assets in runtime projection |
| `tests` | `object` | `true` | `` | test references |
| `tests.test_doc` | `string` | `true` | `pattern=^/Users/albus/MyProjects/ANC_v2/.+` | skill test doc path |
| `tests.methodology_ref` | `string` | `true` | `pattern=^/Users/albus/MyProjects/ANC_v2/.+` | test methodology reference |

示例条目：

```json
{
  "skill_id": "meta.qa.llm-judge",
  "name": "llm-judge",
  "path": "/Users/albus/MyProjects/ANC_v2/skills/meta/llm-judge/SKILL.md",
  "layer": "meta",
  "owner": "qa",
  "version": "0.1.0",
  "status": "draft",
  "agentskills": {
    "name": "llm-judge",
    "description": "Evaluate outputs against objective/spec and return structured verdict",
    "license": "Apache-2.0",
    "compatibility": {
      "openclaw": ">=2026.2",
      "agentskills": ">=0.2"
    }
  },
  "openclaw": {
    "projection_mode": "bundle",
    "bundle_key": "anc-v2-meta-skills",
    "bundle_source": "/Users/albus/MyProjects/ANC_v2/skills/meta",
    "entry_key": "meta.qa.llm-judge",
    "source": "/Users/albus/MyProjects/ANC_v2/skills/meta/llm-judge",
    "install_strategy": "lazy",
    "allow_draft_projection": true
  },
  "tests": {
    "test_doc": "/Users/albus/MyProjects/ANC_v2/skills/meta/llm-judge/TEST.md",
    "methodology_ref": "/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md"
  }
}
```

## process_registry.json

- schema_version: `1.1.0`
- updated_at: `2026-02-21T18:00:00Z`
- strict mode: `true`

| 字段 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| `process_id` | `string` | `true` | `pattern=^[a-z0-9-]+$` | stable process identifier |
| `skill_name` | `string` | `true` | `pattern=^[a-z0-9-]+$` | process skill frontmatter name |
| `skill_path` | `string` | `true` | `pattern=^/Users/albus/MyProjects/ANC_v2/.+` | absolute process SKILL.md path |
| `manifest_path` | `string` | `true` | `pattern=^/Users/albus/MyProjects/ANC_v2/.+` | absolute process manifest path |
| `objective_ref` | `string` | `true` | `` | objective identifier |
| `owner` | `string` | `true` | `` | owner agent_id |
| `version` | `string` | `true` | `pattern=^[0-9]+\.[0-9]+\.[0-9]+$` | semantic version |
| `status` | `string` | `true` | `enum=draft,review,active,deprecated,retired` | lifecycle status |
| `phase_count` | `integer` | `true` | `min=1` | declared phase count |
| `openclaw` | `object` | `true` | `` | OpenClaw projection metadata |
| `openclaw.projection_mode` | `string` | `true` | `enum=bundle,pin,off` | projection strategy |
| `openclaw.entry_key` | `string` | `true` | `` | stable OpenClaw entry key |
| `openclaw.source` | `string` | `true` | `pattern=^/Users/albus/MyProjects/ANC_v2/.+` | OpenClaw source path |
| `openclaw.bundle_key` | `string` | `false` | `` | bundle key when projection_mode=bundle |
| `openclaw.bundle_source` | `string` | `false` | `pattern=^/Users/albus/MyProjects/ANC_v2/.+` | bundle source when projection_mode=bundle |
| `openclaw.allow_draft_projection` | `boolean` | `false` | `` | allow draft assets in runtime projection |

示例条目：

```json
{
  "process_id": "development-process",
  "skill_name": "development-process",
  "skill_path": "/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/SKILL.md",
  "manifest_path": "/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/process.json",
  "objective_ref": "obj-phase1-min-loop",
  "owner": "bpm",
  "version": "0.1.0",
  "status": "draft",
  "phase_count": 4,
  "openclaw": {
    "projection_mode": "bundle",
    "bundle_key": "anc-v2-meta-processes",
    "bundle_source": "/Users/albus/MyProjects/ANC_v2/processes/meta",
    "entry_key": "development-process",
    "source": "/Users/albus/MyProjects/ANC_v2/processes/meta/development-process",
    "allow_draft_projection": true
  }
}
```

## 校验命令

```bash
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py validate
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py generate-docs --check
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py project-openclaw --all --check
```
