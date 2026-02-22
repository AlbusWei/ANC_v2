# M2 — BPM 引擎模块详细设计

> 版本: v0.7.0 | 建设优先级: P0 | 最后更新: 2026-02-22

## 模块定位

`M2` 是 ANC 的流程运行时与触发运行时中枢，负责流程实例调度、触发治理执行、证据链留痕与升级闭环。  
`M2` 不负责策略生命周期治理，策略治理由 `M4` 管理。

相关文档：

1. `docs/design/skills/bpm-runtime-skills.md`
2. `docs/design/processes/trigger-schedule-runtime-process.md`
3. `docs/design/processes/trigger-event-runtime-process.md`
4. `docs/design/modules/trigger-governance-test-proposal.md`
5. `docs/design/modules/trigger-governance-review-checklist.md`
6. `docs/design/processes/governance-processes.md`

## 模块边界

1. `M2` 只负责运行时编排，不负责触发策略生命周期管理。
2. `M2` 不持有系统级高权限写操作能力。
3. 涉及系统级写操作时，固定由 admin 执行，`M2` 负责门禁与编排留痕。
4. App/owner 请求不得直达 admin，必须走 BPM 升级链。

## 组件与落盘状态

| 组件 | 目标技能/资产 | 状态 |
|---|---|---|
| process parser | `sys.bpm.process-instance-manager` 子能力 | 已并入 |
| instance manager | `sys.bpm.process-instance-manager` | 已落盘（review） |
| scheduler | `sys.bpm.process-instance-manager` 子能力 | 已并入 |
| evidence recorder | `sys.bpm.evidence-recorder` | 已落盘（draft，可执行） |
| recursion lineage guard | `sys.bpm.process-instance-manager` 子能力 | 已并入 |
| trigger ingress normalizer | `sys.bpm.trigger-ingress-normalizer` | 已落盘（draft，可执行） |
| trigger matcher + dedupe ledger | `sys.bpm.trigger-matcher-dedupe` | 已落盘（draft，可执行） |
| catchup scheduler | `sys.bpm.catchup-scheduler` | 已落盘（draft，可执行） |
| escalation handler | `sys.bpm.escalation-handler` | 已落盘（draft，可执行） |

## 本轮已补齐的流程资产

1. `trigger-schedule-runtime`（P4）
2. `trigger-event-runtime`（P4）
3. AP-026~AP-031（触发归一、匹配去重、调度、证据、补跑、升级）
4. `governed-config-change`（P4，W2 可执行闭环：gate -> apply -> verify -> rollback）

## 递归能力

1. 支持 `parent_instance_id`, `lineage_ref`, `stack_depth`。
2. 支持 parent/child 实例隔离，输出按契约回填。
3. 强制会话绑定：`session_binding.json` 固化 `agent_id/session_key/session_id/parent_session_id`。
4. BPM 调度调用必须显式传 `--session-id`。
5. 超深度递归或上下文泄漏触发 Fail-Closed。

## 触发运行时能力

1. 支持 `schedule|heartbeat|event|threshold` 触发类型。
2. 外部事件先标准化为 canonical trigger，再执行匹配。
3. 去重采用分层策略：
   - 主键：`source + event_id`
   - 回退键：`source + canonical_event + entity_type + entity_id + from_status + to_status + emitted_by + time_bucket`
4. 漏跑采用动态补跑窗口：由 `catchup_policy_ref` 计算窗口并执行补跑，超窗升级 owner。

最小事件字段：

1. `event_id`
2. `event_time`
3. `entity_type`
4. `entity_id`
5. `from_status`
6. `to_status`
7. `evidence_ref`
8. `emitted_by`
9. `instance_id`

## W3 执行入口与证据

1. Schedule runner：`processes/control/trigger-schedule-runtime/scripts/trigger_schedule_runtime_runner.py`
2. Event runner：`processes/control/trigger-event-runtime/scripts/trigger_event_runtime_runner.py`
3. 回归入口：`tests/m2-bpm-runtime/run_tc_tg.py`
4. 证据汇总：
   - `docs/design/modules/evidence/bpm-runtime/w3_tc_tg_report.json`
   - `docs/design/modules/evidence/bpm-runtime/w3_trigger_runtime_cases/`
   - `docs/design/modules/evidence/bpm-runtime/w3_execution_summary.md`

## Fail-Closed 与安全约束

1. 触发输入字段缺失或证据不可达时拒绝执行。
2. 去重键冲突且无法判定时拒绝执行并升级。
3. 风险无法判定时按高风险处理并升级 admin。
4. 升级链必须满足 `actor -> owner -> bpm -> admin -> human`。

## 流程收口策略

1. 可执行层保持双流程：`trigger-schedule-runtime` + `trigger-event-runtime`。
2. 仅在触发家族明显扩展或公共治理逻辑显著增厚时，引入上级 `trigger-runtime-supervisor`（P5 路由模式）。

后验参数治理：

1. `catchup_policy_ref`、`time_bucket_strategy` 等动态参数不在 `M2` 文档内直接硬编码定值。
2. 必须进入 `runtime-policy-calibration` 治理流程，由 `kernel/system-analyst` 做后验分析并同步给 `architect/admin/bpm` 决策。
3. `runtime-policy-calibration` 运行入口：`processes/meta/runtime-policy-calibration/scripts/runtime_policy_calibration_runner.py`。
4. 生产回归入口：`tests/m2-bpm-runtime/run_tc_anl.py`（覆盖 `TC-ANL-001~003`）。

## 验收清单

- [x] P4 流程可组合 P5/P6 并执行
- [x] 父子实例不共享可变上下文
- [x] 触发与实例可双向追溯
- [x] TG-SCH-001/002/003/004 具备运行级证据
- [x] TG-EVT-001/002/003 具备运行级证据
- [x] 动态 catchup 策略已在运行证据中验证
- [x] TC-GCC-001/002/003 具备运行级证据（真实 patch + rollback + 拒绝分支）
