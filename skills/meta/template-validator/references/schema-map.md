# template-validator schema 映射表

| 资产类型 | schema 入口 | 校验重点 |
|---|---|---|
| Skill | `shared/registry/skill_registry.json` | frontmatter 与 tests 对齐 |
| Process | `shared/registry/process_registry.json` | phase 字段与 control_flow 闭合 |
| Agent | `shared/registry/agent_directory.json` | owner、workspace、lifecycle 一致 |

## 使用规则

1. 校验时优先使用对应 registry 的 `entry_contract`。
2. 资产 schema 与 registry contract 冲突时，按 contract Fail-Closed。
