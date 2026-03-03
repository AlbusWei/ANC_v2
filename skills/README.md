# Skills Directory

## Layout

1. `skills/template/`：模板资产（脚手架）。
2. `skills/skill-creator/`：本地化技能生成与评审标准样板。
3. `skills/meta/{objective-writer,agent-creator,process-creator,template-validator,spec-writer,test-designer,llm-judge}/`：M3 元技能资产。
4. `skills/system/qa/*`：M1 质量门禁技能资产（test-compiler/evaluation-runner/verdict-normalizer/hold-triage/regression-runner/registry-validator/evidence-archiver）。
5. `skills/system/entire-codex-sync/`：Entire x Codex 同步桥接技能。
6. `skills/system/{trigger-ingress-normalizer,trigger-matcher-dedupe,process-instance-manager,evidence-recorder,catchup-scheduler,escalation-handler}/`：M2 BPM runtime 技能资产。
7. `skills/system/construction-audit/`：M6 施工联动审计技能资产。
8. `skills/system/superpower-sync/`：M6 Superpower 协同同步技能资产。
9. `skills/system/git-worktree-sync/`：多 worktree 分支集成与扇出同步技能资产。

## Rule

- `template` 目录不注册到 registry。
- 非模板目录必须包含可解析 `SKILL.md`，并在 `skill_registry.json` 可发现。
- QA 门禁技能统一维护在 `skills/system/qa/` 子目录。
