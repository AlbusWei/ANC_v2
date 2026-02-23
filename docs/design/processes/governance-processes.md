# 治理流程清单与设计

> 版本: v1.4.0 | 分类: Governance Processes

## 核心治理流程

1. lifecycle-review
2. registry-sync
3. escalation
4. governed-config-change
5. hold-governance
6. trigger-schedule-runtime
7. trigger-event-runtime
8. trigger-runtime-supervisor（P5 模式，规划）
9. runtime-policy-calibration（P5 治理模式，可执行）
10. construction-plane-governance

## lifecycle-review（可执行资产，review）

设计文档：`docs/design/processes/lifecycle-review-process.md`
流程资产：`processes/meta/lifecycle-review/process.json`
运行入口：`processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py`
owner：`hr`（`system-analyst` 仅提供分析输入，不作为 owner）

状态证据：

1. `docs/design/modules/evidence/quality-gate/runtime-validation-round-6-m1-closure/TC-M1-CHAIN-001/lifecycle_output.json`
2. `docs/design/modules/evidence/quality-gate/runtime-validation-round-6-m1-closure/TC-M1-CHAIN-001/lifecycle/lifecycle_review_report.json`

阶段：

1. validate-request
2. check-prerequisites
3. quality-gate
4. execute-transition
5. sync-registry

输入契约：

1. `final_gate_verdict_ref`
2. `target_asset_ref`
3. `requested_transition`

输出契约：

1. `lifecycle_transition_ref`
2. `registry_sync_ref`
3. `lifecycle_review_report_ref`

状态规则：`draft -> review -> active -> deprecated -> retired`

Fail-Closed：

1. 非法状态迁移直接拒绝。
2. 证据缺失或不可解析直接拒绝。
3. registry 校验失败直接阻断。

## registry-sync（P6 原子语义，可执行资产）

设计文档：`docs/design/processes/registry-sync-process.md`  
流程资产：`processes/meta/registry-sync/process.json`  
运行入口：`processes/meta/registry-sync/scripts/registry_sync_runner.py`

定位：

1. AP-011 的治理包装流程，负责 registry 同步与校验证据输出。
2. 固定保持 P6 原子口径，不升级为 P5/P4 复合流程。

输入契约：

1. `target_registry_ref`
2. `registry_patch_plan_ref`
3. `requested_transition_ref`
4. `verify_scope`
5. `evidence_ref`

输出契约：

1. `registry_sync_ref`
2. `registry_verify_report_ref`
3. `sync_decision`
4. `reasons`

Fail-Closed：

1. patch plan 缺失或不可解析 -> `fail`
2. registry verify 非零退出 -> `fail`
3. 证据不可追溯 -> `blocked`

test_mount：

1. `tests/m3-runtime/run_skill_contract_validation.py`（统一入口）
2. `python3 shared/registry/registry_contract_tool.py verify`（合规门禁）

生命周期：`draft`（Session3 已落地，保持不越级）

## escalation（P5 模式，可执行资产）

设计文档：`docs/design/processes/escalation-process.md`  
流程资产：`processes/meta/escalation/process.json`  
运行入口：`processes/meta/escalation/scripts/escalation_runner.py`

固定升级链：`actor -> owner -> bpm -> admin -> human`

phase 映射：

1. `incident-intake`（AP-013）
2. `policy-check`（AP-031 前置校验）
3. `chain-routing`（AP-031）
4. `resolution-or-human`（AP-025）

输入契约：

1. `incident_ref`
2. `severity`
3. `current_owner`
4. `escalation_policy_ref`
5. `evidence_ref`

输出契约：

1. `escalation_ref`
2. `escalation_trace`
3. `final_owner`
4. `escalation_decision`
5. `reasons`

Fail-Closed：

1. 升级链不完整或越级 -> `fail`
2. incident/evidence 缺失 -> `fail`
3. policy 冲突不可裁决 -> `blocked`

test_mount：

1. `tests/m3-runtime/run_skill_contract_validation.py`（统一入口）
2. `python3 shared/registry/registry_contract_tool.py verify`（注册链路一致性）

生命周期：`draft`（Session3 已落地，保持不越级）

## M3 AP 包装流程族（Session3 新增）

为消除 `full-development/hotfix/refactor` phase 直连 skill，本回合新增 7 个 AP 包装流程：

1. `ap-001-002-003-bundle`
2. `ap-001-002-bundle`
3. `ap-003-004-bundle`
4. `ap-004-bundle`（绑定 `meta.arch.spec-writer`）
5. `ap-006-bundle`（绑定 `system.ops.manual-task`）
6. `ap-012-bundle`（绑定 `sys.admin.release-manager`）
7. `ap-013-014-015-017-bundle`

约束：

1. 上述流程均固定为 P6 最小可调度骨架。
2. 生命周期统一保持 `draft`。
3. 仅承担 AP 包装语义，不在本回合扩展复杂业务逻辑。

## governed-config-change

阶段：

1. intake-and-normalize（bpm）
2. gate-and-risk-classification（bpm）
3. authorize-change（admin）
4. execute-config-change（admin）
5. verify-and-archive（bpm）

约束：

1. 系统级配置写操作只能由 admin 执行。
2. 执行前必须完成 objective/spec/test 与 rollback 证据校验。
3. 执行后必须记录 hash_before/hash_after 与回滚状态。

运行入口与测试：

1. 执行入口：`processes/meta/governed-config-change/scripts/governed_config_change_runner.py`
2. P2 门禁 runner：`skills/system/config-change-gatekeeper/scripts/config_change_gatekeeper_runner.py`
3. P4 执行 runner：`skills/system/system-config-updater/scripts/system_config_updater_runner.py`
4. 运行级用例：`tests/m2-bpm-runtime/TC-GCC.md`（`TC-GCC-001~003`）

## hold-governance

设计文档：`docs/design/processes/hold-governance-process.md`

阶段：

1. collect-progress-evidence（AP-021）
2. triage-and-classify（AP-022）
3. execute-triage-action（AP-023）
4. health-maintenance（AP-024）
5. close-or-escalate（AP-025）

关键约束：

1. 禁止以固定超时阈值直接判定失败。
2. triage 必须基于三类进展信号（日志增量/阶段推进/输出流心跳）。
3. triage 必须产出 `continue/retry/debug/fail` 之一。
4. 升级链固定为 `qa -> bpm -> admin`。

## trigger-schedule-runtime

设计文档：`docs/design/processes/trigger-schedule-runtime-process.md`
策略参考：`docs/design/processes/trigger-runtime-policy-guidelines.md`

阶段：

1. normalize-trigger-ingress（AP-026）
2. match-and-dedupe（AP-027）
3. dispatch-instance（AP-028）
4. record-trigger-evidence（AP-029）
5. schedule-catchup（AP-030）
6. escalate-runtime-anomaly（AP-031）

## trigger-event-runtime

设计文档：`docs/design/processes/trigger-event-runtime-process.md`
策略参考：`docs/design/processes/trigger-runtime-policy-guidelines.md`

阶段：

1. normalize-event-ingress（AP-026）
2. match-and-dedupe（AP-027）
3. dispatch-instance（AP-028）
4. record-trigger-evidence（AP-029）
5. request-backfill-or-catchup（AP-030）
6. escalate-runtime-anomaly（AP-031）

## construction-plane-governance

设计文档：`docs/design/processes/construction-plane-governance-process.md`
协同协议：`docs/design/interfaces/openspec-collaboration-protocol.md`
owner：`architect`（语义），`bpm`（编排执行）

阶段：

1. scope-intake-and-baseline（AP-032 / manual-task）
2. run-construction-audit（AP-033 / sys.arch.construction-audit）
3. execute-linked-updates（AP-034 / manual-task）
4. sync-openspec-state（AP-035 / system.integration.openspec-sync）
5. verify-and-close（AP-036 / manual-task）

关键约束：

1. 模块/layer 变更必须触发联动审计并输出 `linkage_report_ref`。
2. design/inventory/registry/施工平面四类联动项必须同回合闭合。
3. 架构相关变更必须完成 OpenSpec 双向映射并产出 `openspec_sync_ref`。
4. `openspec_sync_ref` 必须满足 `openspec-collaboration-schema.json` 完整 schema。
5. `registry_contract_tool.py verify` 失败时禁止关闭回合。
6. 开放问题必须落盘 owner 与下一步动作。
7. 巡检采用“变更触发 + system-analyst 可调频巡检”，不固定周频。
8. 回合契约固定为 `1 round = 1 OpenSpec change = N Entire checkpoints = N commits`。

## trigger-runtime-supervisor（P5 模式，规划）

定位：

1. 作为可选上级路由流程，统一入口并按 `trigger_type` 分发到 `trigger-schedule-runtime` 或 `trigger-event-runtime`。
2. 仅在触发家族明显增多或跨触发治理逻辑增厚时启用。
3. 模式定义见：`docs/design/processes/trigger-runtime-supervisor-pattern.md`。

## runtime-policy-calibration（P5 治理模式，可执行）

定位：

1. 统一承接“需要运营后验分析才可形成实证结论”的参数与策略议题。
2. 由 `kernel/system-analyst` 主责分析，并同步给 `architect/admin/bpm` 做治理决策。
3. 模式定义见：`docs/design/processes/runtime-policy-calibration-process.md`。

运行入口与测试：

1. 执行入口：`processes/meta/runtime-policy-calibration/scripts/runtime_policy_calibration_runner.py`
2. 核心技能：`skills/system/system-feedback-digest/scripts/system_feedback_digest_runner.py`
3. 运行级用例：`tests/m2-bpm-runtime/TC-ANL.md`（`TC-ANL-001~003`）

适用议题：

1. M1 测试执行时长估计与门禁参数校准。
2. M2 动态 `catchup_policy_ref` 校准与 `time_bucket_strategy` 调整。
3. 其他依赖运行观测后验结论的治理参数问题。

## Fail-Closed

1. 无权限或证据不足直接拒绝。
2. 状态迁移非法直接拒绝。
3. registry 不一致直接阻断。
4. 配置变更后健康检查失败且回滚失败时直接升级 human。
5. HOLD triage 无有效进展证据且无法补证时直接失败并升级。
6. trigger 去重冲突不可判定时直接失败并升级。
7. 后验分析样本不足时，禁止输出参数更新结论并保持现行策略。
8. 施工联动项缺失或开放问题无 owner 时，禁止将回合标记 Done。
9. OpenSpec 与 ANC 文档语义冲突未裁决时，禁止关闭施工回合。
