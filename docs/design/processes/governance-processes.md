# 治理流程清单与设计

> 版本: v1.0.0 | 分类: Governance Processes

## 核心治理流程

1. lifecycle-review
2. registry-sync
3. escalation
4. governed-config-change
5. hold-governance
6. trigger-schedule-runtime
7. trigger-event-runtime
8. trigger-runtime-supervisor（P5 模式，规划）
9. runtime-policy-calibration（P5 治理模式，规划）
10. construction-plane-governance

## lifecycle-review

阶段：

1. validate-request
2. check-prerequisites
3. quality-gate
4. execute-transition
5. sync-registry

状态规则：`draft -> review -> active -> deprecated -> retired`

## escalation

升级链：`actor -> owner -> bpm -> admin -> human`

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

## hold-governance

设计文档：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/hold-governance-process.md`

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

设计文档：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/trigger-schedule-runtime-process.md`
策略参考：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/trigger-runtime-policy-guidelines.md`

阶段：

1. normalize-trigger-ingress（AP-026）
2. match-and-dedupe（AP-027）
3. dispatch-instance（AP-028）
4. record-trigger-evidence（AP-029）
5. schedule-catchup（AP-030）
6. escalate-runtime-anomaly（AP-031）

## trigger-event-runtime

设计文档：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/trigger-event-runtime-process.md`
策略参考：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/trigger-runtime-policy-guidelines.md`

阶段：

1. normalize-event-ingress（AP-026）
2. match-and-dedupe（AP-027）
3. dispatch-instance（AP-028）
4. record-trigger-evidence（AP-029）
5. request-backfill-or-catchup（AP-030）
6. escalate-runtime-anomaly（AP-031）

## construction-plane-governance

设计文档：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/construction-plane-governance-process.md`
协同协议：`/Users/albus/MyProjects/ANC_v2/docs/design/interfaces/openspec-collaboration-protocol.md`
owner：`architect`（语义），`bpm`（编排执行）

阶段：

1. scope-intake-and-baseline（manual-task）
2. run-construction-audit（sys.arch.construction-audit）
3. execute-linked-updates（manual-task）
4. sync-openspec-state（system.integration.openspec-sync）
5. verify-and-close（manual-task）

关键约束：

1. 模块/layer 变更必须触发联动审计并输出 `linkage_report_ref`。
2. design/inventory/registry/施工平面四类联动项必须同回合闭合。
3. 架构相关变更必须完成 OpenSpec 双向映射并产出 `openspec_sync_ref`。
4. `openspec_sync_ref` 必须满足 `openspec-collaboration-schema.json` 完整 schema。
5. `registry_contract_tool.py verify` 失败时禁止关闭回合。
6. 开放问题必须落盘 owner 与下一步动作。
7. 巡检采用“变更触发 + system-analyst 可调频巡检”，不固定周频。

## trigger-runtime-supervisor（P5 模式，规划）

定位：

1. 作为可选上级路由流程，统一入口并按 `trigger_type` 分发到 `trigger-schedule-runtime` 或 `trigger-event-runtime`。
2. 仅在触发家族明显增多或跨触发治理逻辑增厚时启用。
3. 模式定义见：`docs/design/processes/trigger-runtime-supervisor-pattern.md`。

## runtime-policy-calibration（P5 治理模式，规划）

定位：

1. 统一承接“需要运营后验分析才可形成实证结论”的参数与策略议题。
2. 由 `kernel/system-analyst` 主责分析，并同步给 `architect/admin/bpm` 做治理决策。
3. 模式定义见：`docs/design/processes/runtime-policy-calibration-process.md`。

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
