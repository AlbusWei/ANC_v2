# 触发治理测试提案（Phase 1 草案）

> 版本: v0.1.0 | 状态: Draft | 范围: 文档设计提案（不含运行资产开发）

## 1. 目标与边界

本提案用于定义“触发治理”最小可评审测试集合，验证以下目标：

1. 调度触发与事件触发可被统一治理并可审计。
2. 系统优先自维持，常规决策不依赖 human master 介入。
3. 高风险行为具备留档、checkpoint 与回滚路径。

本提案明确不包含：

1. 不新增可执行 `process.json` 资产。
2. 不修改 OpenClaw 运行配置。
3. 不新增/变更 registry 条目（仅定义设计要求）。

## 2. 设计基线（本轮已确认）

1. `P1~P3` 作为 Governance Module，`P4~P6` 作为 Executable Flow。
2. 触发规则独立治理，采用 `trigger_registry`（与 `process_registry` 解耦）。
3. M2/M4 边界固定：M2 管触发运行时，M4 管触发策略生命周期。
4. 升级链固定：`actor -> owner -> bpm -> admin -> human`。
5. 去重策略固定：混合去重（`event_id` 优先，缺失回退业务语义键）。
6. 漏跑策略固定：补跑优先（窗口内自动补跑，超窗升级 owner）。
7. 安全边界固定：
   - App/owner 不得直达 admin。
   - BPM 不持有系统高权限写操作能力。
   - 系统级写操作由 admin 审批并执行。

## 3. 测试场景 A：3 分钟定时汇报（仅异常推送）

### 3.1 触发定义

1. `trigger_type`: `schedule`
2. `schedule`: `*/3 * * * *`
3. `target_process`: `p4-admin-ops-report`（规划）
4. `delivery_policy`: `exception-only`（无异常仅记录执行账本）

### 3.2 执行链路

`schedule trigger -> bpm -> analyst summary -> admin -> human`

### 3.3 验收用例

| Case ID | 输入条件 | 预期行为 | 必备证据 |
|---|---|---|---|
| TG-SCH-001 | 3 分钟窗口内存在异常 | 创建实例并推送异常摘要到 admin；admin 转发 human | `trigger_log_ref`, `instance_ref`, `admin_forward_ref` |
| TG-SCH-002 | 3 分钟窗口无异常 | 不推送消息，仅记录心跳执行账本 | `trigger_ledger_ref` |
| TG-SCH-003 | owner 取消当次任务 | 不执行实例，输出 override 审计记录 | `override_decision_ref`, `override_reason_ref` |
| TG-SCH-004 | 计划窗口内漏跑一次 | 在 `catchup_window` 内自动补跑并保留补跑标记 | `catchup_run_ref`, `catchup_reason_ref` |

## 4. 测试场景 B：Skill 生命周期变更触发证据归集

### 4.1 触发定义

1. `trigger_type`: `event`
2. `canonical_event`: `internal.lifecycle.transitioned`
3. `match_rule`: `entity_type=skill && from_status=review && to_status=active`
4. `target_process`: `p4-kernel-lifecycle-evidence-collect`（规划）

### 4.2 事件最小字段

1. `event_id`
2. `event_time`
3. `entity_type`
4. `entity_id`
5. `from_status`
6. `to_status`
7. `transition_evidence_ref`
8. `emitted_by`
9. `instance_id`

### 4.3 执行链路

`lifecycle transition event -> trigger matcher -> bpm -> system-analyst evidence collect -> admin summary`

### 4.4 验收用例

| Case ID | 输入条件 | 预期行为 | 必备证据 |
|---|---|---|---|
| TG-EVT-001 | Skill `review -> active` 事件到达 | 命中规则并创建归集实例 | `event_ref`, `instance_ref` |
| TG-EVT-002 | 同一事件重复投递 | 按混合去重拒绝重复执行 | `dedupe_key_ref`, `dedupe_reject_log` |
| TG-EVT-003 | 缺少 `transition_evidence_ref` | Fail-Closed，不输出结论性摘要，触发补数请求 | `fail_closed_record`, `backfill_request_ref` |

## 5. 治理与审计要求

1. 任一 override、补跑、去重拒绝都必须有独立证据条目。
2. 高风险触发执行前必须建立 checkpoint，失败时可回滚。
3. 触发事件与流程实例必须可双向追溯（`trigger_id` <-> `instance_id`）。

## 6. 下一步（仅文档）

1. 在 L2/L4 文档固化触发治理边界与角色分工。
2. 在 M2/M4 文档固化运行时/策略治理拆分。
3. 在层间接口契约补充 Trigger/Hook 入口与 Fail-Closed 约束。
4. 使用评审清单模板执行逐项审查：
`docs/design/modules/trigger-governance-review-checklist.md`
