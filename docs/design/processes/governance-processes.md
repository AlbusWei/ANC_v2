# 治理流程清单与设计

> 版本: v1.5.0 | 分类: Governance Processes

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
owner：`hr`

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

## escalation（P5 模式，可执行资产）

设计文档：`docs/design/processes/escalation-process.md`
流程资产：`processes/meta/escalation/process.json`
运行入口：`processes/meta/escalation/scripts/escalation_runner.py`

固定升级链：`actor -> owner -> bpm -> admin -> human`

## M3 P5 子流程族（Session3/Phase2）

为统一 M3 主流程编排语义，现行子流程族如下：

1. `objective-scope-baseline`
2. `hotfix-intake-normalization`
3. `hotfix-scope-spec-baseline`
4. `spec-authoring-contract`（绑定 `meta.arch.spec-writer`）
5. `implementation-execution-core`（绑定 `system.ops.manual-task`）
6. `release-packaging-governed`（绑定 `sys.admin.release-manager`）
7. `evolution-feedback-planning`

约束：

1. 上述流程为 P5 可复用子流程，生命周期在本回合保持 `draft`。
2. 历史包装流程已退役，不得作为目标态运行单元回流。
3. 主流程 phase 仅允许依赖已注册子流程并保持 I/O 闭合。

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

设计文档：`docs/design/processes/hold-governance-process.md`

阶段：

1. collect-progress-evidence（AP-021）
2. triage-and-classify（AP-022）
3. execute-triage-action（AP-023）
4. health-maintenance（AP-024）
5. close-or-escalate（AP-025）

## trigger-schedule-runtime

设计文档：`docs/design/processes/trigger-schedule-runtime-process.md`
策略参考：`docs/design/processes/trigger-runtime-policy-guidelines.md`

## trigger-event-runtime

设计文档：`docs/design/processes/trigger-event-runtime-process.md`
策略参考：`docs/design/processes/trigger-runtime-policy-guidelines.md`

## construction-plane-governance

设计文档：`docs/design/processes/construction-plane-governance-process.md`
协同协议：`docs/design/interfaces/openspec-collaboration-protocol.md`
owner：`architect`（语义），`bpm`（编排执行）

关键约束：

1. 模块/layer 变更必须触发联动审计并输出 `linkage_report_ref`。
2. design/inventory/registry/施工平面四类联动项必须同回合闭合。
3. `registry_contract_tool.py verify` 失败时禁止关闭回合。

## trigger-runtime-supervisor（P5 模式，规划）

定位：

1. 作为可选上级路由流程，统一入口并按 `trigger_type` 分发到 `trigger-schedule-runtime` 或 `trigger-event-runtime`。
2. 仅在触发家族明显增多或跨触发治理逻辑增厚时启用。
