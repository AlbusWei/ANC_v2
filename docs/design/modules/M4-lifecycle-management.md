# M4 — 生命周期管理模块详细设计

> 版本: v0.3.1 | 建设优先级: P1

## 模块定位

管理 Agent/Skill/Process 的 5 态生命周期与审批证据，并治理触发策略生命周期。

## 状态机

`draft -> review -> active -> deprecated -> retired`

## 组件

1. lifecycle-transition
2. permission-checker
3. registry-validator
4. lifecycle-review
5. trigger-policy-manager
6. override-decision-recorder

## lifecycle-review 最小可执行接点（M1 -> M4）

1. owner 固定为 `hr`（`system-analyst` 仅提供分析输入，不作为 owner）。
2. 生命周期状态：`draft`（后续线程基于运行证据推进到 `review/active`）。
3. 流程资产：`processes/meta/lifecycle-review/process.json`
4. 运行入口：`processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py`
5. 输入契约最小集：`final_gate_verdict_ref`、`target_asset_ref`、`requested_transition`
6. 输出契约最小集：`lifecycle_transition_ref`、`registry_sync_ref`、`lifecycle_review_report_ref`

## 触发策略治理资产（规划）

1. `trigger_registry`：维护 trigger 定义与生命周期（与 process_registry 解耦）。
2. `trigger_override_log`：记录 owner/admin 的取消、延期、豁免决策。
3. `trigger_policy_review`：对高风险触发策略做审批与复核。

## 约束

1. review 前不得 active。
2. active 不得直接 retired。
3. 每次转换必须有 evidence_ref。
4. owner 的取消/延期动作必须留痕且可审计。
5. 高风险策略必须声明 checkpoint 与回滚要求。
6. 策略治理与执行分离：M4 管策略，M2 管执行。

## 验收

- [ ] 非法状态迁移被拒绝
- [ ] 状态与 registry 同步
- [ ] 审批链完整
- [ ] trigger 策略可独立进入 review/active 并可回滚
- [ ] override 决策均有 evidence_ref 与责任人
