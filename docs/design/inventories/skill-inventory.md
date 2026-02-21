# Skill 全量清单

> 版本: v0.9.0 | SSOT: `shared/registry/skill_registry.json`

## 已注册 Skill

1. meta.qa.llm-judge
2. meta.arch.spec-writer
3. meta.qa.test-designer
4. meta.arch.skill-creator
5. meta.arch.objective-writer
6. meta.arch.agent-creator
7. meta.arch.process-creator
8. meta.arch.template-validator
9. system.integration.entire-codex-sync
10. system.ops.manual-task
11. system.control.config-change-gatekeeper
12. system.admin.system-config-updater
13. sys.bpm.trigger-ingress-normalizer
14. sys.bpm.trigger-matcher-dedupe
15. sys.bpm.process-instance-manager
16. sys.bpm.evidence-recorder
17. sys.bpm.catchup-scheduler
18. sys.bpm.escalation-handler
19. sys.arch.construction-audit
20. system.integration.openspec-sync

## 规划 Skill（节选）

- sys.hr.lifecycle-transition
- sys.hr.permission-checker
- sys.qa.registry-validator
- sys.qa.regression-runner
- sys.qa.test-compiler
- sys.qa.evaluation-runner
- sys.qa.verdict-normalizer
- sys.qa.hold-triage
- sys.admin.release-manager

## 技能粒度决策（M2）

1. `sys.bpm.process-parser`、`sys.bpm.process-scheduler`、`sys.bpm.lineage-guard` 已决策并入 `sys.bpm.process-instance-manager` 子能力，不再独立注册。

Quality Gate 技能包设计文档：

- `docs/design/skills/quality-gate-skills.md`

BPM Runtime 技能包设计文档：

- `docs/design/skills/bpm-runtime-skills.md`

Self-Development 技能包设计文档：

- `docs/design/skills/self-development-skills.md`

Construction Plane 技能包设计文档：

- `docs/design/skills/construction-plane-skills.md`

## 生命周期规则

统一 5 态并由 lifecycle-review 驱动迁移。
