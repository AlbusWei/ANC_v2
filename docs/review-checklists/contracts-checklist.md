# Contracts Review Checklist

> Branch: `codex/review-contracts`
> Worktree: `review-contracts`

## 1. 目标

完成协议统一与硬切收口，确保 BPM I/O、Context Protocol、Role Handoff、Process Manifest 与 registry 门禁一致且可机器校验。

## 2. Entire 执行要求（每次会话）

1. `entire status --detailed`
2. `python3 skills/system/entire-codex-sync/scripts/entire_codex_bridge.py start`
3. 有改动回合后执行 `sync`（带 `--prompt/--summary/--files`）
4. `git commit` 后检查 `Entire-Checkpoint`
5. `python3 skills/system/entire-codex-sync/scripts/entire_codex_bridge.py end`

## 3. 本轮范围

1. `docs/architecture/process_architecture.md`
2. `docs/architecture/context_protocol.md`
3. `docs/design/interfaces/bpm-actor-protocol.md`
4. `docs/design/data-models/context-schemas.md`
5. `docs/design/data-models/process-instance-schemas.md`
6. `docs/design/interfaces/role-handoff-protocol.md`
7. `processes/meta/development-process/process.json`
8. `processes/meta/governed-config-change/process.json`
9. `shared/registry/registry_contract_tool.py`
10. `shared/registry/*.json`
11. `config/openclaw.phase05*.json`
12. `docs/review-checklists/contracts-field-mapping.md`

## 4. 核对项

1. 所有路径字段统一为 canonical 根相对路径（禁止绝对路径与 `..`）。
2. `task_dispatch` 统一为 `target_type + target_id`，`target_id` 强绑定 registry 稳定 ID。
3. `task_completion.self_check` 固定 `decision/reason/rule_refs`，且 `rule_refs` 为 `repo_relative_path#anchor`。
4. `phase.requires_spec` 已落地，`requires_spec=true` 时 `spec_ref` 必填。
5. process manifest 无双轨字段：禁止 `control`/`failure_policy`、禁止 `skill*` 旧别名。
6. `check-protocol-consistency` 已接入 `verify`，fail-closed 生效。
7. `contracts-field-mapping.md` 已落盘并可追溯字段裁决来源。

## 5. 完成定义（DoD）

1. `jq empty` 三个 registry 均通过。
2. `python3 shared/registry/registry_contract_tool.py check-protocol-consistency` 通过。
3. `python3 shared/registry/registry_contract_tool.py verify` 通过。
4. 反向注入旧字段后门禁可稳定失败（fail-closed）。
5. Checklist 与 mapping 文档证据链接闭环。
