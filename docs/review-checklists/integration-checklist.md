# Integration Review Checklist

> Branch: `codex/review-integration`
> Worktree: `/Users/albus/MyProjects/ANC_v2_worktrees/review-integration`
> Baseline Commit: `d2d7699`

## 1. 目标

核对跨层集成一致性：流程协议、数据契约、registry 门禁、技能与流程复用链路是否可联调、可回放、可审计。

## 2. 集成锚点（SSOT）

1. `/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/architecture/context_protocol.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/design/interfaces/bpm-actor-protocol.md`
4. `/Users/albus/MyProjects/ANC_v2/docs/design/data-models/process-instance-schemas.md`
5. `/Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py`

## 3. 当前进度（d2d7699）

- [x] 合约一致性校验链已内建到 `registry_contract_tool.py verify`。
- [x] 质量门禁与 HOLD 治理的流程/原子/技能设计链路已文档化。
- [x] Trigger governance 具备文档级 dry-run 证据。
- [ ] 端到端运行级联调证据（非文档模拟）尚未完成。
- [ ] 集成回放脚本与固定样例输入输出集尚未冻结。

## 4. 核对项

- [ ] BPM dispatch/completion 字段与 schema 完全一致，无旧别名残留。
- [ ] `target_type + target_id` 均能命中 registry 稳定 ID。
- [ ] `process.json` 的 `process_level/control_flow/fail_policy/lineage_policy` 可被工具链校验。
- [ ] 关键流程链路 `quality-gate-preparation -> AP-006 -> quality-gate-evaluation -> hold-governance` 可回放。
- [ ] evidence 目录结构与 `process-instance-schemas.md` 要求一致。

## 5. 完成定义（DoD）

- [ ] 至少 1 条完整开发链路完成运行级 dry-run 并沉淀证据。
- [ ] `python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify` 持续通过。
- [ ] 集成问题清单（发现/影响/修复/回归）闭环落盘。

## 6. 提交前校验

1. `entire status --detailed`
2. `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py sync --prompt "..." --summary "..." --files ...`
3. `python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify`
4. `git log -1 --pretty=raw`（确认 `Entire-Checkpoint`）
