# Skill 全量清单

> 版本: v1.0.0 | SSOT: `shared/registry/skill_registry.json`

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
21. system.ops.git-worktree-sync
22. sys.qa.test-compiler
23. sys.qa.evaluation-runner
24. sys.qa.verdict-normalizer
25. sys.qa.hold-triage
26. sys.qa.regression-runner
27. sys.qa.registry-validator
28. sys.qa.evidence-archiver
29. sys.arch.system-feedback-digest

## 规划 Skill（节选）

- sys.hr.lifecycle-transition
- sys.hr.permission-checker
- sys.arch.impact-analyzer
- sys.admin.release-manager

## 技能粒度决策（M2）

1. `sys.bpm.process-parser`、`sys.bpm.process-scheduler`、`sys.bpm.lineage-guard` 已决策并入 `sys.bpm.process-instance-manager` 子能力，不再独立注册。

Quality Gate 技能包设计文档：

- `docs/design/skills/quality-gate-skills.md`
- 运行级验证证据：`docs/design/modules/evidence/quality-gate/runtime-validation-round-2.md`
- 严格模型配置验证证据：`docs/design/modules/evidence/quality-gate/runtime-validation-round-3.md`
- LLM-as-Judge 跑通验证证据：`docs/design/modules/evidence/quality-gate/runtime-validation-round-4.md`

BPM Runtime 技能包设计文档：

- `docs/design/skills/bpm-runtime-skills.md`

Self-Development 技能包设计文档：

- `docs/design/skills/self-development-skills.md`

Construction Plane 技能包设计文档：

- `docs/design/skills/construction-plane-skills.md`

Git Operations 技能包设计文档：

- `docs/design/skills/git-operations-skills.md`

## 生命周期规则

统一 5 态并由 lifecycle-review 驱动迁移。

W1 变更记录（M2 BPM Runtime Hardening）：

1. `sys.bpm.process-instance-manager` 生命周期由 `draft` 推进到 `review`（不推进到 `active`）。

W2 变更记录（M2 BPM Runtime Hardening）：

1. `system.control.config-change-gatekeeper` 新增可执行 runner：`skills/system/config-change-gatekeeper/scripts/config_change_gatekeeper_runner.py`。
2. `system.admin.system-config-updater` 新增可执行 runner：`skills/system/system-config-updater/scripts/system_config_updater_runner.py`。
3. 两项技能 registry 版本由 `0.1.0` 升级到 `0.2.0`，生命周期保持 `draft`。

W3 变更记录（M2 BPM Runtime Hardening）：

1. `sys.bpm.trigger-ingress-normalizer` 新增 runner：`skills/system/trigger-ingress-normalizer/scripts/trigger_ingress_normalizer_runner.py`。
2. `sys.bpm.trigger-matcher-dedupe` 新增 runner：`skills/system/trigger-matcher-dedupe/scripts/trigger_matcher_dedupe_runner.py`。
3. `sys.bpm.evidence-recorder` 新增 runner：`skills/system/evidence-recorder/scripts/evidence_recorder_runner.py`。
4. `sys.bpm.catchup-scheduler` 新增 runner：`skills/system/catchup-scheduler/scripts/catchup_scheduler_runner.py`。
5. `sys.bpm.escalation-handler` 新增 runner：`skills/system/escalation-handler/scripts/escalation_handler_runner.py`。
6. 上述 5 项技能 registry 版本由 `0.1.0` 升级到 `0.2.0`，生命周期保持 `draft`。

W5 变更记录（M2 BPM Runtime Hardening）：

1. 新增 `sys.arch.system-feedback-digest` 可执行 runner：`skills/system/system-feedback-digest/scripts/system_feedback_digest_runner.py`。
2. `system-analyst` 生产链路改为调用 `sys.arch.system-feedback-digest` 输出 `digest/reject`。
3. 运行级验证入口：`tests/m2-bpm-runtime/run_tc_anl.py`（覆盖 `TC-ANL-001~003`）。
