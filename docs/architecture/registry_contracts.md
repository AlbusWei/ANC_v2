# ANC v2 Registry 契约

最后更新：2026-02-18  
版本：2.0.0-alpha

> 本文件定义三类注册表的字段、格式和与 OpenClaw/Agent Skills 的映射关系。

## 1. 设计目标

1. 可发现：按 ID/名称快速定位资产与路径。
2. 可治理：支持版本、状态、owner、生命周期追踪。
3. 可对接：能映射到 OpenClaw 配置和 Agent Skills frontmatter。

## 2. skill_registry.json

`entries[]` 推荐字段：

1. `skill_id`: 稳定唯一标识（建议 `layer.domain.name`）。
2. `name`: 与 `SKILL.md` frontmatter 的 `name` 一致。
3. `path`: `SKILL.md` 绝对路径。
4. `layer`: `meta` / `system` / `business`。
5. `owner`: 责任角色或 Agent ID。
6. `version`: 语义化版本。
7. `status`: `draft` / `active` / `deprecated` / `retired`。
8. `agentskills`: frontmatter 摘要（`description`, `license`, `compatibility`）。
9. `openclaw`: 加载映射（`entry_name`, `source`, `install_strategy`）。
10. `tests`: 对应测试文件与方法论路径。

## 3. process_registry.json

`entries[]` 推荐字段：

1. `process_id`: 稳定唯一标识。
2. `skill_name`: 对应 `processes/<name>/SKILL.md` 的 frontmatter `name`。
3. `skill_path`: process Skill 文档路径。
4. `manifest_path`: `process.json` 路径。
5. `objective_ref`: 对齐目标 ID。
6. `owner`: 流程 owner。
7. `version`: 语义化版本。
8. `status`: 生命周期状态。
9. `phase_count`: Phase 数量。
10. `openclaw`: 是否纳入 `skills.entries` 及加载信息。

## 4. agent_directory.json

`entries[]` 推荐字段：

1. `agent_id`: 唯一标识。
2. `layer`: `kernel` / `control` / `app`。
3. `path`: Agent 根目录路径。
4. `default_model`: 默认模型。
5. `owner`: 责任人或上级 Agent。
6. `status`: 生命周期状态。
7. `bindings`: OpenClaw channel 绑定信息。
8. `permissions`: 权限级别摘要。
9. `skills`: 允许调用的 skill_id 列表。

## 5. 与 OpenClaw 的映射

1. registry 中的 `openclaw.entry_name` 对应 `skills.entries[].name`。
2. registry 中 `agent_id` 对应 OpenClaw `agents.list` 的条目键。
3. registry 的 `bindings` 对应 `channels`/`channelsConfig` 绑定策略。

## 6. 与 Agent Skills 规范映射

每个技能/流程 Skill 的 `SKILL.md` frontmatter 至少应含：

1. `name`
2. `description`
3. `license`
4. `compatibility`

registry 应镜像这些关键字段，避免运行时与文档脱钩。

## 7. 验证建议

1. JSON 语法校验：`jq . <file>`。
2. 路径存在性校验：遍历 `path`/`manifest_path`。
3. 名称一致性校验：registry `name` 与 frontmatter `name` 对齐。
4. 版本一致性校验：registry `version` 与文档版本对齐。

## 8. 参考链接

1. OpenClaw Gateway Configuration：https://docs.openclaw.ai/gateway/configuration
2. OpenClaw CLI：https://docs.openclaw.ai/cli/index
3. Agent Skills 规范：https://agentskills.io/specification
