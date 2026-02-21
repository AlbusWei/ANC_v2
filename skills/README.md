# Skills Directory

## Layout

1. `skills/template/`：模板资产（脚手架）。
2. `skills/skill-creator/`：真实示例（meta skill）。
3. `skills/system/entire-codex-sync/`：Entire x Codex 同步桥接技能。
4. `skills/system/{test-compiler,evaluation-runner,verdict-normalizer,regression-runner,hold-triage}/`：M1 质量门禁技能组。
5. `skills/system/{process-instance-manager,escalation-handler}/`：HOLD 治理 BPM 协同技能。

## Rule

- `template` 目录不注册到 registry。
- 非模板目录必须包含可解析 `SKILL.md`，并在 `skill_registry.json` 可发现。
