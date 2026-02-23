# 系统技能清单与设计

> 版本: v1.0.0 | 分类: System Skills | 层级: L2 | 最后更新: 2026-02-22

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
22. system.control.config-change-gatekeeper
23. system.admin.system-config-updater
24. sys.arch.system-feedback-digest

## 技能包路径约定

1. QA 门禁技能统一放置在 `skills/system/qa/*`。
2. 其他系统技能保持 `skills/system/<skill-name>/`。

## BPM Runtime 技能包

统一 BPM runtime 技能设计见：

- `docs/design/skills/bpm-runtime-skills.md`

## Config Governance 技能包

配置治理执行链（W2）：

1. `system.control.config-change-gatekeeper`
2. `system.admin.system-config-updater`
3. `processes/meta/governed-config-change/scripts/governed_config_change_runner.py`（流程执行入口）

## Quality Gate 技能包

统一质量门禁技能设计见：

- `docs/design/skills/quality-gate-skills.md`
- `docs/design/modules/evidence/quality-gate/runtime-validation-round-2.md`
- `docs/design/modules/evidence/quality-gate/runtime-validation-round-3.md`
- `docs/design/modules/evidence/quality-gate/runtime-validation-round-4.md`

## Construction Plane 技能包

统一施工面治理技能设计见：

- `docs/design/skills/construction-plane-skills.md`

## Runtime Policy Calibration 技能包

后验策略校准分析技能（W5）：

1. `sys.arch.system-feedback-digest`
2. `processes/meta/runtime-policy-calibration/scripts/runtime_policy_calibration_runner.py`（流程执行入口）

## Git Operations 技能包

统一 Git worktree 协同技能设计见：

- `/Users/albus/MyProjects/ANC_v2/docs/design/skills/git-operations-skills.md`

## 目标

提供治理、编排、回归、发布的系统级能力。

治理补充：

1. 对于需后验运营分析的问题，优先由 `sys.arch.impact-analyzer` + `system-analyst` 进入 `runtime-policy-calibration` 流程输出治理提案。

## M3 Session2 设计闭合定义卡（待实现）

### 1. sys.arch.impact-analyzer

- 定位：在元层与流程层变更前执行影响面分析与回滚需求评估，为架构裁决提供结构化输入。
- 输入契约：
  - `change_proposal_ref`
  - `affected_scope_ref`
  - `risk_constraints_ref`
  - `evidence_ref`（可选，若已有历史运行证据）
- 输出契约：
  - `impact_report_ref`
  - `risk_level`（`low|medium|high|critical`）
  - `rollback_requirements`
  - `gating_recommendation`（`allow|hold|reject`）
- Fail-Closed：
  - 变更提案不可解析 -> `reject`
  - 影响范围证据不可达 -> `hold`
  - 风险约束冲突且无裁决记录 -> `reject`
- test_mount（计划字段）：
  - `tests/m3-self-development/TC-IMPACT-ANALYZER.md`
  - `tests/m3-self-development/run_tc_online.py --case TC-IMPACT-ANALYZER-001`
- 生命周期预期：`draft`（Session2 设计闭合，Session3 落运行资产）

### 2. sys.admin.release-manager

- 定位：在发布阶段统一执行发布包组装、变更日志生成、发布决策与回滚包约束校验。
- 输入契约：
  - `candidate_artifacts_ref`
  - `final_gate_verdict_ref`
  - `lifecycle_transition_ref`
  - `registry_sync_ref`
  - `release_policy_ref`（可选）
- 输出契约：
  - `release_package_ref`
  - `changelog_ref`
  - `release_decision`（`approved|rejected|blocked`）
  - `rollback_bundle_ref`
- Fail-Closed：
  - 任一前置门禁证据缺失 -> `rejected`
  - `registry_sync_ref` 校验失败 -> `blocked`
  - 回滚包不可用 -> `rejected`
- test_mount（计划字段）：
  - `tests/m3-self-development/TC-RELEASE-MANAGER.md`
  - `tests/m3-self-development/run_tc_online.py --case TC-RELEASE-MANAGER-001`
- 生命周期预期：`draft`（Session2 设计闭合，Session3 落运行资产）

## 生命周期

统一 5 态治理，并由 lifecycle-review 控制激活。
