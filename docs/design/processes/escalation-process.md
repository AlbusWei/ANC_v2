# escalation 流程设计

> 版本: v0.1.0 | 分类: Governance Process | 层级: P5 | 类型: 可复用治理子流程 | process_id: escalation | owner: bpm | 生命周期: draft

## 目标

沉淀统一升级治理模式，为开发、测试、发布、运行时异常提供一致的升级链执行语义与证据输出，避免各流程各自定义升级规则导致漂移。

## 定位与边界

1. `escalation` 定位为 P5 可复用治理子流程，不直接承担业务交付输出。
2. 本流程负责升级链路执行与证据留痕，不替代具体流程的业务决策。
3. 仅在出现异常、冲突或权限不足时触发，不作为常规主链路阶段。

## 固定升级链

`actor -> owner -> bpm -> admin -> human`

约束：

1. 禁止越级升级。
2. 任一级成功处理后必须输出终止决策并结束流程。
3. 升级到 `human` 后禁止自动回退到机器角色继续推进。

## phase 定义与 AP 映射

1. `incident-intake`（AP-013）
   - 目标：标准化异常输入、锁定范围与初始责任人。
2. `policy-check`（AP-031 前置校验）
   - 目标：校验升级策略、权限边界与证据完备度。
3. `chain-routing`（AP-031）
   - 目标：按升级链路路由并记录每级决策痕迹。
4. `resolution-or-human`（AP-025）
   - 目标：输出闭环决策（解决、继续升级或转人工）。

## 输入契约

必填字段：

1. `incident_ref`
2. `severity`
3. `current_owner`
4. `escalation_policy_ref`
5. `evidence_ref`

校验规则：

1. `severity` 仅允许 `low|medium|high|critical`。
2. `current_owner` 必须在升级链角色集合中。
3. `escalation_policy_ref` 必须声明可达升级终点与超时策略。

## 输出契约

1. `escalation_ref`
2. `escalation_trace`
3. `final_owner`
4. `escalation_decision`（`resolved|escalated|human_required|failed`）
5. `reasons`

## Fail-Closed

1. `incident_ref` 或 `evidence_ref` 缺失时直接 `fail`。
2. 升级链不完整、越级或循环路由时直接 `fail`。
3. `escalation_policy_ref` 不可解析或与当前流程冲突时 `blocked`。
4. 在 `critical` 场景下无法触达 `admin/human` 时直接 `fail` 并冻结流程。

## test_mount（计划字段）

1. `tests/m3-self-development/TC-ESCALATION-P5.md`
2. `tests/m3-self-development/run_tc_online.py --case TC-ESCALATION-P5-001`

## 复用方（首批）

1. `full-development`（异常回填路径）
2. `hotfix`（高优先级异常升级）
3. `refactor`（治理冲突升级）
4. `trigger-schedule-runtime` / `trigger-event-runtime`（运行时异常升级）
5. `hold-governance`（`close-or-escalate` 回填）

## 生命周期与推进规则

1. 本文档阶段：设计闭合（`draft`）。
2. Session3 才允许新增 `processes/meta/escalation/` 运行资产与 registry 实条目。
3. 未完成运行级回归前，禁止推进到 `review/active`。

