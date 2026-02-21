# ANC v2 Registry 契约

最后更新：2026-02-21  
版本：2.2.0-alpha

> 本文件定义三类 registry 的治理约束，以及 registry 到 OpenClaw 的投影规则。

## 0. 决策索引

本文件的架构动机与可复用决策见：

`/Users/albus/MyProjects/ANC_v2/docs/architecture/registry_governance_decisions.md`

阅读顺序建议：

1. 先看决策文档（为什么这样设计）。
2. 再看本文件（如何落为可执行约束）。

## 1. 设计目标

1. 可发现：按稳定 ID 快速定位资产。
2. 可治理：状态、owner、版本、测试引用可追溯。
3. 可投影：可从 registry 自动生成运行时受管配置。
4. Fail-Closed：字段不合法或证据不足时拒绝写入。

## 2. 机器真相源（SSOT）

1. 每个 registry 文件中的 `entry_contract` 是机器真相源。
2. `entry_contract` 必须包含：
   - `required`
   - `properties`
   - `additionalProperties: false`
3. 人类可读 schema 文档由工具生成，不得手工漂移：
   - `/Users/albus/MyProjects/ANC_v2/docs/design/data-models/registry-schemas.md`

## 3. 统一生命周期（强制）

所有 registry 统一 5 态：

`draft -> review -> active -> deprecated -> retired`

迁移规则：

1. `draft` 进入正式审查时必须显式转换到 `review`。
2. 仅 `review` 可进入 `active`。
3. `active` 不可直接 `retired`，必须先 `deprecated`。

## 4. agent_directory.json

`entries[]` 关键字段：

1. `agent_id`
2. `layer`
3. `path`
4. `default_model`
5. `owner`
6. `status`
7. `permissions`（`string[]`）
8. `bindings`（对象：`channels[]` + `channelsConfig`）

## 5. skill_registry.json

`entries[]` 关键字段：

1. `skill_id`
2. `name`
3. `path`
4. `layer`
5. `owner`
6. `version`
7. `status`
8. `agentskills`（含 `name/description/license/compatibility`）
9. `openclaw`
10. `tests`

`openclaw` 关键子字段：

1. `projection_mode`: `bundle|pin|off`
2. `entry_key`: 稳定投影键（pin 时必须等于 `skill_id`）
3. `source`
4. `install_strategy`
5. `bundle_key`（bundle 模式）
6. `bundle_source`（bundle 模式）
7. `allow_draft_projection`（可选）

## 6. process_registry.json

`entries[]` 关键字段：

1. `process_id`
2. `skill_name`
3. `skill_path`
4. `manifest_path`
5. `objective_ref`
6. `owner`
7. `version`
8. `status`
9. `phase_count`
10. `openclaw`

`openclaw.entry_key` 在 pin 模式必须等于 `process_id`。

### canonical 约束

`development-process` 的 canonical 路径：
`/Users/albus/MyProjects/ANC_v2/processes/meta/development-process`

## 7. Registry 到 OpenClaw 的投影规则

投影目标文件：

1. `/Users/albus/MyProjects/ANC_v2/config/openclaw.phase05.fragment.json`
2. `/Users/albus/MyProjects/ANC_v2/config/openclaw.phase05.with-entry.fragment.json`

受管区仅包含：

1. `agents.list`
2. `skills.entries`

状态门禁：

1. `agent`：`draft/review/active` 允许投影。
2. `skill/process`：默认仅 `review/active`。
3. `skill/process` 为 `draft` 时，必须 `openclaw.allow_draft_projection=true`。
4. `deprecated/retired` 默认不投影。

冲突规则：

1. 支持 `bundle + pin` 混合投影。
2. 同时命中时，pin 优先。

## 8. 投影 profile

profile 文件：

`/Users/albus/MyProjects/ANC_v2/config/openclaw.projection.profiles.json`

profile 定义：

1. 输出文件路径。
2. 参与投影的 agent 清单。
3. agent 状态白名单。

## 9. 验证命令

```bash
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py validate
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py generate-docs --check
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py project-openclaw --all --check
python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify
```
