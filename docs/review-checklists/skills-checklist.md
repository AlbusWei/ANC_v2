# Skills Review Checklist

> Branch: `codex/review-skills`
> Worktree: `../review-skills`

## 1. 目标

核对 meta/system/business 技能定义一致性、测试挂载点与生命周期门禁。

## 2. Entire 执行要求（每次会话）

1. `entire status --detailed`
2. `.../entire_codex_bridge.py start`
3. 每回合改动后 `sync`
4. commit 后检查 `Entire-Checkpoint`
5. `.../entire_codex_bridge.py end`

## 3. 允许修改范围

1. `docs/design/skills/`
2. `docs/design/inventories/skill-inventory.md`
3. 可选：`skills/skill-creator/SKILL.md`（仅在确需对齐时）

## 4. 禁止修改范围

1. `docs/design/agents/`
2. `docs/design/business/`
3. `shared/registry/`

## 5. 核对项

1. 元技能/系统技能/业务技能分类边界清晰。
2. 所有 `skills/**/SKILL.md` 均包含 `Capability Contract (Machine-Readable)` YAML 块并可解析。
3. 技能定义中输入/输出契约可验证（含 machine_judgement 字段）。
4. Fail-Closed 规则存在且可执行。
5. 生命周期使用统一 5 态，且 `draft -> review` 必须通过 Capability Contract 校验。
6. 测试文档挂载点与说明一致（`SKILL.md.test_mount` 与 registry `tests` 一致）。
7. skill-inventory 条目与技能设计文档一致。
8. `entire-codex-sync` 作为系统技能的定位一致。

## 6. 完成定义（DoD）

1. 形成“技能契约差异清单”并关闭。
2. `python3 shared/registry/registry_contract_tool.py verify` 通过。
3. 测试路径引用可达。
4. 提交仅包含 skills 与 skill inventory 相关文件（如有跨域修改须在变更说明中注明原因）。

## 7. 建议提交粒度

1. `skills: contract and lifecycle alignment`
2. `skills: inventory and test-mount consistency`
