# Contracts Review Checklist

> Branch: `codex/review-contracts`
> Worktree: `../review-contracts`

## 1. 目标

完成契约与数据模型的一致性核对，确保生命周期、递归流程、BPM 协议和 registry 字段闭环。

## 2. Entire 执行要求（每次会话）

1. `entire status --detailed`
2. `python3 skills/system/entire-codex-sync/scripts/entire_codex_bridge.py start`
3. 有改动回合后执行 `sync`（带 prompt/summary/files）
4. `git commit` 后检查 `Entire-Checkpoint`
5. `python3 skills/system/entire-codex-sync/scripts/entire_codex_bridge.py end`

## 3. 允许修改范围

1. `docs/architecture/process_architecture.md`
2. `docs/architecture/registry_contracts.md`
3. `docs/design/data-models/`
4. `docs/design/interfaces/`
5. `shared/registry/`
6. `config/`

## 4. 禁止修改范围

1. `docs/design/agents/`
2. `docs/design/skills/`
3. `docs/design/business/`
4. `docs/design/processes/atomic/`

## 5. 核对项

1. 生命周期 5 态在三 registry 与契约文档完全一致。
2. `process_level`, `parent_process_id`, `composed_processes`, `lineage_policy` 字段定义一致。
3. `parent_instance_id`, `lineage_ref`, `stack_depth` 在 BPM 协议与 context/process schema 一致。
4. `development-process` canonical/legacy 路径说明一致。
5. schema 字段命名与示例 JSON 一致（无别名漂移）。
6. Fail-Closed 条件在 process/bpm/context 三处表述不冲突。
7. registry 字段与 design/data-models/registry-schemas.md 一致。
8. 所有引用路径均可达。
9. `openclaw.phase05*.json` 的 `agents.list` / `skills.entries` 与 registry 投影一致。

## 6. 完成定义（DoD）

1. 通过 `jq` 校验三 registry JSON。
2. 输出一份“契约差异清单”并全部关闭。
3. 提交只包含本分支允许范围内文件。
4. `registry_contract_tool.py verify` 通过。

## 7. 建议提交粒度

1. `contracts: lifecycle and schema alignment`
2. `contracts: bpm/context recursion field unification`
