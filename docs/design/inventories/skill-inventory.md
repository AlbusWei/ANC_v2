# Skill 全量清单

> 版本: v1.6.0 | SSOT: `shared/registry/skill_registry.json`

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
20. system.integration.superpower-sync
21. system.ops.git-worktree-sync
22. sys.qa.test-compiler
23. sys.qa.evaluation-runner
24. sys.qa.verdict-normalizer
25. sys.qa.hold-triage
26. sys.qa.regression-runner
27. sys.qa.registry-validator
28. sys.qa.evidence-archiver
29. sys.arch.system-feedback-digest
30. sys.arch.impact-analyzer
31. sys.admin.release-manager

运行名映射说明：

1. `meta.arch.skill-creator` 的仓库内运行名为 `meta-skill-creator`。
2. `skill-creator` 仅保留历史别名说明，不用于仓库内调用指令。

## 规划 Skill（节选）

| skill_id | 规划状态 | 生命周期目标 | test_mount（计划） |
|---|---|---|---|
| sys.hr.lifecycle-transition | 规划中（未闭合） | draft | TBA |
| sys.hr.permission-checker | 规划中（未闭合） | draft | TBA |

## M3 Session3 已落地 Skill

| skill_id | 实现状态 | 生命周期 | test_mount |
|---|---|---|---|
| sys.arch.impact-analyzer | 已落地 `SKILL.md/TEST.md/runner` 并完成契约联测 | draft | `skills/system/impact-analyzer/TEST.md` + `tests/m3-runtime/run_skill_contract_validation.py` |
| sys.admin.release-manager | 已落地 `SKILL.md/TEST.md/runner` 并完成契约联测 | draft | `skills/system/release-manager/TEST.md` + `tests/m3-runtime/run_skill_contract_validation.py` |

## 技能粒度决策（M2）

1. `sys.bpm.process-parser`、`sys.bpm.process-scheduler`、`sys.bpm.lineage-guard` 已决策并入 `sys.bpm.process-instance-manager` 子能力，不再独立注册。

Quality Gate 技能包设计文档：

- `docs/design/skills/quality-gate-skills.md`
- 运行级验证证据：`runtime_data/execution/evidence/quality-gate/runtime-validation-round-2.md`
- 严格模型配置验证证据：`runtime_data/execution/evidence/quality-gate/runtime-validation-round-3.md`
- LLM-as-Judge 跑通验证证据：`runtime_data/execution/evidence/quality-gate/runtime-validation-round-4.md`

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
3. `sys.arch.system-feedback-digest` 生命周期状态为 `review`（本轮不推进 `active`）。
4. 运行级验证入口：`tests/m2-bpm-runtime/run_tc_anl.py`（覆盖 `TC-ANL-001~003`）。

W6 变更记录（m3-meta-asset-quality-hardening Phase3）：

1. 8 个目标元技能（`meta.arch.*` + `meta.qa.*`）统一升级为执行级资产（触发矩阵、字段级 I/O、Fail-Closed 决策表、运行命令）。
2. `meta.arch.agent-creator`、`meta.arch.process-creator`、`meta.arch.template-validator`、`meta.arch.skill-creator` 新增/升级统一 CLI runner（`--input/--output/[--report]`，返回码 `0/2/1`）。
3. `meta.arch.skill-creator` 运行名切换为 `meta-skill-creator`，`skill-creator` 在仓库内软禁用（仅历史别名说明）。
4. 8 个目标元技能生命周期统一推进到 `review`（不推进到 `active`）。

W7 变更记录（m3-meta-asset-quality-hardening Phase4）：

1. Phase4 联动复核确认：8 个目标元技能状态保持 `review`，本轮不推进 `active`。
2. `meta.arch.skill-creator` 的仓库内运行入口保持 `meta-skill-creator`；`skill-creator` 仅用于历史别名追溯。
3. `shared/registry/skill_registry.json` 完成核对且无字段增量（no-delta）。

W8 变更记录（M3 协作骨架扩展：full-development）：

1. `sys.bpm.process-instance-manager` 新增会话治理能力：`--reset-openclaw-session`、`--strict-session-match`。
2. `sys.bpm.process-instance-manager` registry 版本由 `0.1.0` 升级到 `0.2.0`，生命周期保持 `review`。

W9 变更记录（M3 流程标准一致性收口）：

1. `meta.arch.process-creator` runner 升级为 canonical 校验口径，拒绝 legacy 字段并强制 `inline_ap`/`spec_ref` 规则。
2. `meta.arch.process-creator` registry 版本由 `0.2.0` 升级到 `0.3.0`，生命周期保持 `review`。
3. `sys.bpm.process-instance-manager` manifest 校验增强（`subprocess + inline_ap + spec_ref anchor`）。
4. `sys.bpm.process-instance-manager` registry 版本由 `0.2.0` 升级到 `0.3.0`，生命周期保持 `review`。

W14 变更记录（M3 流程执行语义补全）：

1. `sys.bpm.process-instance-manager` 新增 phase 分发语义落盘（`task_dispatch/dispatch_context/dispatch_prompt`）。
2. `sys.bpm.process-instance-manager` registry 版本由 `0.3.0` 升级到 `0.4.0`，生命周期保持 `review`。
3. `system.ops.manual-task` 从“人工兜底”改为“Actor 通用执行入口”，支持 BPM dispatch 输入并产出 `task_completion` 留档。
4. `system.ops.manual-task` registry 版本由 `0.1.0` 升级到 `0.2.0`，生命周期保持 `draft`。
