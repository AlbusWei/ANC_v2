# BPM Runtime Skills 设计包

> 版本: v0.3.0 | 分类: System Skills | 模块: M2 BPM Engine | 最后更新: 2026-02-22

## 目标

定义 `M2` 触发运行时与流程实例治理技能集合，覆盖归一、匹配、去重、补跑、升级、证据归档与实例管理。

关联文档：

1. `docs/design/modules/M2-bpm-engine.md`
2. `docs/design/processes/trigger-schedule-runtime-process.md`
3. `docs/design/processes/trigger-event-runtime-process.md`
4. `docs/design/modules/trigger-governance-test-proposal.md`
5. `docs/design/processes/trigger-runtime-policy-guidelines.md`

## 技能粒度原则（本轮结论）

1. `process-parser / process-scheduler / lineage-guard` 不再拆分为独立 Skill。
2. 三者并入 `sys.bpm.process-instance-manager` 作为子能力（manifest 解析、调度计划、lineage 守卫）。
3. 设计优先级：能力闭环与上下文装载效率优先于“过细拆分”。

## 技能定义卡（本轮落盘）

### 1. sys.bpm.trigger-ingress-normalizer

- 定位：统一 `schedule|heartbeat|event|threshold` 触发输入为 canonical envelope。
- 输入契约：`trigger_type`, `trigger_source`, `payload_ref`, `received_at`
- 输出契约：`canonical_trigger_ref`, `trigger_id`, `normalization_report_ref`
- Fail-Closed：类型不支持、字段缺失、payload 不可达。
- test_mount：`skills/system/trigger-ingress-normalizer/TEST.md`

### 2. sys.bpm.trigger-matcher-dedupe

- 定位：规则匹配 + 幂等去重，防止重复实例。
- 输入契约：`canonical_trigger_ref`, `match_policy_ref`, `dedupe_policy_ref`
- 输出契约：`match_result`, `dedupe_decision`, `dedupe_key_ref`, `matcher_evidence_ref`
- 去重策略：
  - 主键：`source + event_id`
  - 回退键：`source + canonical_event + entity_type + entity_id + from_status + to_status + emitted_by + time_bucket`
  - 若主键和回退键都无法构造或冲突不可判定，Fail-Closed。
- test_mount：`skills/system/trigger-matcher-dedupe/TEST.md`

### 3. sys.bpm.process-instance-manager

- 定位：实例创建、状态推进、父子上下文隔离，并内含 parser/scheduler/lineage 子能力。
- 输入契约：`process_id`, `phase_id`, `instance_context_ref`, `lineage_ref`, `stack_depth`, `process_version`, `process_level`, `session_binding`
- 输出契约：`instance_id`, `runtime_state`, `state_transition_ref`, `evidence_ref`
- 子能力：
  - `manifest-parse`：校验 process manifest 与 phase 闭合
  - `phase-schedule`：基于 control_flow 生成调度决策
  - `lineage-guard`：执行递归深度与上下文隔离约束
- Fail-Closed：phase 不存在、上下文泄漏、递归深度超限、manifest 不闭合、会话绑定缺失或父子会话复用。
- test_mount：`skills/system/process-instance-manager/TEST.md`

### 4. sys.bpm.evidence-recorder

- 定位：统一触发运行时证据条目，维护 trigger/instance 双向追溯。
- 输入契约：`trigger_id`, `instance_id`, `decision`, `evidence_payload_ref`
- 输出契约：`trigger_receipt_ref`, `evidence_index_ref`, `traceability_link_ref`
- Fail-Closed：关键 ID 缺失、证据元字段缺失、追溯链生成失败。
- test_mount：`skills/system/evidence-recorder/TEST.md`

### 5. sys.bpm.catchup-scheduler

- 定位：漏跑补跑调度，基于动态策略计算补跑窗口并输出升级建议。
- 输入契约：`missed_run_ref`, `catchup_policy_ref`, `trigger_policy_ref`, `runtime_state_ref`
- 输出契约：`catchup_decision`, `catchup_run_ref`, `catchup_reason_ref`, `escalation_hint`
- 动态窗口：由 `catchup_policy_ref` 按 `trigger_type/risk_level/runtime_history` 计算，不使用固定时长。
- Fail-Closed：漏跑证据缺失、决策不明确、动态窗口不可计算。
- test_mount：`skills/system/catchup-scheduler/TEST.md`

### 6. sys.bpm.escalation-handler

- 定位：按固定升级链执行异常升级。
- 输入契约：`incident_ref`, `escalation_policy_ref`, `current_owner`, `evidence_ref`
- 输出契约：`escalation_ref`, `final_owner`, `escalation_decision`, `escalation_trace`
- Fail-Closed：升级链缺段、越级、无证据升级。
- test_mount：`skills/system/escalation-handler/TEST.md`

## 流程收口策略（设计建议）

1. 可执行层保持 `trigger-schedule-runtime` 与 `trigger-event-runtime` 双流程，保证输入契约清晰、Fail-Closed 边界明确。
2. 如后续触发家族增加（>2）或跨触发治理逻辑显著增长，再引入 `trigger-runtime-supervisor`（P5 上级路由模式）。

## 生命周期与落盘状态

1. 本轮状态：`sys.bpm.process-instance-manager` 已推进到 `review`；其余 5 个核心技能保持 `draft`。
2. 已决策并入：`process-parser/process-scheduler/lineage-guard` 不再单独注册。
3. 激活前置：
   - `registry_contract_tool.py verify` 通过
   - 与 `trigger-schedule-runtime` / `trigger-event-runtime` 的 I/O 契约一致
   - 完成至少一轮运行级 dry-run 证据
