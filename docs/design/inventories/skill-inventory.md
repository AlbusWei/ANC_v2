# Skill 全量清单

> 版本: v0.5.0 | SSOT: `shared/registry/skill_registry.json`

## 已注册 Skill（registry entries）

1. meta.qa.llm-judge
2. meta.arch.spec-writer
3. meta.qa.test-designer
4. system.integration.entire-codex-sync
5. system.ops.manual-task
6. system.control.config-change-gatekeeper
7. system.admin.system-config-updater
8. sys.qa.test-compiler
9. sys.qa.evaluation-runner
10. sys.qa.verdict-normalizer
11. sys.qa.regression-runner
12. sys.qa.hold-triage
13. sys.bpm.process-instance-manager
14. sys.bpm.escalation-handler

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
- sys.admin.release-manager

## 质量门禁技能组（M1）

1. `sys.qa.test-compiler`
2. `sys.qa.evaluation-runner`
3. `sys.qa.verdict-normalizer`
4. `sys.qa.regression-runner`
5. `sys.qa.hold-triage`

关联设计文档：

- `docs/design/skills/quality-gate-skills.md`

## 生命周期规则

统一 5 态并由 lifecycle-review 驱动迁移。
