# Skill 全量清单

> 版本: v0.6.0 | SSOT: `shared/registry/skill_registry.json`

## 已注册 Skill

1. meta.qa.llm-judge
2. meta.arch.spec-writer
3. meta.qa.test-designer
4. system.integration.entire-codex-sync
5. system.ops.manual-task
6. system.control.config-change-gatekeeper
7. system.admin.system-config-updater
8. sys.bpm.trigger-ingress-normalizer
9. sys.bpm.trigger-matcher-dedupe
10. sys.bpm.process-instance-manager
11. sys.bpm.evidence-recorder
12. sys.bpm.catchup-scheduler
13. sys.bpm.escalation-handler

## 待注册但已落盘

1. skill-creator

## 规划 Skill（节选）

- meta.arch.objective-writer
- meta.arch.agent-creator
- meta.arch.process-creator
- meta.arch.template-validator
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

## 生命周期规则

统一 5 态并由 lifecycle-review 驱动迁移。
