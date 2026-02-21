# Skills Directory

## Layout

1. `skills/template/`：模板资产（脚手架）。
2. `skills/skill-creator/`：真实示例（meta skill）。
3. `skills/system/entire-codex-sync/`：Entire x Codex 同步桥接技能。
4. `skills/system/{trigger-ingress-normalizer,trigger-matcher-dedupe,process-instance-manager,evidence-recorder,catchup-scheduler,escalation-handler}/`：M2 BPM runtime 技能资产。

## Rule

- `template` 目录不注册到 registry。
- 非模板目录必须包含可解析 `SKILL.md`，并在 `skill_registry.json` 可发现。
