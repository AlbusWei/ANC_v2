# Skills Review Checklist

> Branch: `codex/review-skills`
> Worktree: `/Users/albus/MyProjects/ANC_v2_worktrees/review-skills`
> Baseline Commit: `d2d7699`

## 1. 目标

核对技能分层（meta/system/business）、Capability Contract、测试挂载与生命周期治理一致性。

## 2. SSOT 绑定

1. `/Users/albus/MyProjects/ANC_v2/docs/design/skills/skill-lifecycle-protocol.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/design/skills/system-skills.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/design/skills/quality-gate-skills.md`
4. `/Users/albus/MyProjects/ANC_v2/docs/design/inventories/skill-inventory.md`
5. `/Users/albus/MyProjects/ANC_v2/shared/registry/skill_registry.json`

## 3. 当前进度（d2d7699）

- [x] 统一 5 态生命周期规则已落盘（draft/review/active/deprecated/retired）。
- [x] Capability Contract 机器块已纳入校验基线（`registry_contract_tool.py verify`）。
- [x] `quality-gate-skills.md` 已补齐 M1 质量门禁技能设计。
- [ ] 新增系统技能资产（runtime/trigger/lifecycle）仍处在设计与草案阶段。
- [ ] 部分技能的 TEST 证据与 registry `tests` 路径一致性仍需复核。

## 4. 核对项

- [ ] `skills/**/SKILL.md` 均含可解析的 Capability Contract 机器块。
- [ ] `test_mount` 与 registry `tests` 引用一致且路径可达。
- [ ] `skill-inventory.md`、`skill_registry.json`、设计文档三者一致。
- [ ] 生命周期迁移门禁由流程治理驱动，无旁路手动提级。
- [ ] Fail-Closed 规则在技能契约中可执行。

## 5. 完成定义（DoD）

- [ ] 形成“技能契约差异清单”并关闭。
- [ ] `python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify` 通过。
- [ ] 至少 1 条 `draft -> review` 的技能治理链路可回放。

## 6. 提交前校验

1. `entire status --detailed`
2. `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py sync --prompt "..." --summary "..." --files ...`
3. `python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify`
4. `git log -1 --pretty=raw`（确认 `Entire-Checkpoint`）
