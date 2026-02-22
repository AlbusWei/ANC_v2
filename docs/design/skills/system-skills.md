# 系统技能清单与设计

> 版本: v0.8.0 | 分类: System Skills | 层级: L2

## 核心系统技能

1. sys.qa.registry-validator
2. sys.hr.lifecycle-transition
3. sys.hr.permission-checker
4. sys.qa.evidence-archiver
5. sys.bpm.trigger-ingress-normalizer
6. sys.bpm.trigger-matcher-dedupe
7. sys.bpm.process-instance-manager
8. sys.bpm.evidence-recorder
9. sys.bpm.catchup-scheduler
10. sys.bpm.escalation-handler
11. sys.qa.regression-runner
12. sys.arch.impact-analyzer
13. sys.admin.release-manager
14. system.integration.entire-codex-sync
15. sys.qa.test-compiler
16. sys.qa.evaluation-runner
17. sys.qa.verdict-normalizer
18. sys.qa.hold-triage
19. sys.arch.construction-audit
20. system.integration.openspec-sync
21. system.ops.git-worktree-sync

## 技能包路径约定

1. QA 门禁技能统一放置在 `skills/system/qa/*`。
2. 其他系统技能保持 `skills/system/<skill-name>/`。

## BPM Runtime 技能包

统一 BPM runtime 技能设计见：

- `docs/design/skills/bpm-runtime-skills.md`

## Quality Gate 技能包

统一质量门禁技能设计见：

- `docs/design/skills/quality-gate-skills.md`
- `docs/design/modules/evidence/quality-gate/runtime-validation-round-2.md`
- `docs/design/modules/evidence/quality-gate/runtime-validation-round-3.md`
- `docs/design/modules/evidence/quality-gate/runtime-validation-round-4.md`

## Construction Plane 技能包

统一施工面治理技能设计见：

- `docs/design/skills/construction-plane-skills.md`

## Git Operations 技能包

统一 Git worktree 协同技能设计见：

- `/Users/albus/MyProjects/ANC_v2/docs/design/skills/git-operations-skills.md`

## 目标

提供治理、编排、回归、发布的系统级能力。

治理补充：

1. 对于需后验运营分析的问题，优先由 `sys.arch.impact-analyzer` + `system-analyst` 进入 `runtime-policy-calibration` 流程输出治理提案。

## 生命周期

统一 5 态治理，并由 lifecycle-review 控制激活。
