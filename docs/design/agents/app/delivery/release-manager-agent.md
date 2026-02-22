# Release Manager Agent 详细设计

> 版本: v1.0.0 | agent_id: release-manager-agent | 层级: app/delivery | 权限: release-governance | 生命周期: draft（Session2 设计闭合，待 Session3 运行资产落地）

## 1. 角色定位

`release-manager-agent` 是交付链路的发布治理执行节点，负责在门禁通过后完成发布包编排、发布决策输出与回滚包校验，不得绕过生命周期治理。

## 2. bound_skills

1. `sys.admin.release-manager`（核心）
2. `sys.qa.registry-validator`（发布前 registry 合规复核）

## 3. participating_processes

1. `full-development`（`release-packaging` 阶段）
2. `hotfix`（`release-packaging` 阶段）
3. `delivery-iterations`（外部交付复用场景，后续接线）

## 4. handoff 输入契约（release_request_in）

必填字段：

1. `request_id`
2. `objective_ref`
3. `candidate_artifacts_ref`
4. `final_gate_verdict_ref`
5. `lifecycle_transition_ref`
6. `registry_sync_ref`
7. `release_window`
8. `rollback_bundle_ref`
9. `requested_by`
10. `evidence_ref`

校验规则：

1. `final_gate_verdict_ref` 必须为 `pass` 且可追溯。
2. `lifecycle_transition_ref` 与 `registry_sync_ref` 必须同一会话一致。
3. `release_window` 不得为空，且需满足发布策略窗口。

## 5. handoff 输出契约（固定双结构）

### 5.1 成功输出：release_delivery_out

1. `status`（固定 `delivered`）
2. `request_id`
3. `release_package_ref`
4. `changelog_ref`
5. `release_decision`（固定 `approved`）
6. `published_at`
7. `evidence_ref`

### 5.2 拒绝输出：release_reject_out

1. `status`（固定 `rejected`）
2. `request_id`
3. `reason_code`（`gate_failed|registry_invalid|rollback_unavailable|policy_conflict`）
4. `blocking_items`
5. `required_actions`
6. `evidence_ref`

约束：

1. 禁止省略 `release_reject_out` 结构。
2. 任一拒绝必须带 `required_actions`，并可被上游流程消费。

## 6. 权限边界

允许：

1. 读取发布候选包与门禁证据。
2. 生成发布包、变更日志与发布决策。
3. 输出发布拒绝与补救建议。

禁止：

1. 直接修改生命周期状态。
2. 绕过 `lifecycle-review` 执行发布。
3. 执行 OpenClaw 全局配置写操作。

## 7. Fail-Closed

1. 任一前置证据缺失（`gate/lifecycle/registry`）时直接拒绝发布。
2. `rollback_bundle_ref` 不可用时直接拒绝发布。
3. registry 校验返回失败时直接拒绝发布并升级 `owner -> bpm -> admin`。
4. 输出契约字段不完整时禁止向下游交付。

## 8. test_mount（计划字段）

1. `tests/m3-self-development/TC-RELEASE-MANAGER-AGENT.md`
2. `tests/m3-self-development/run_tc_online.py --case TC-RELEASE-MANAGER-AGENT-001`

## 9. DoD（设计闭合口径）

1. 文档内已固定 `release_request_in` 与 `release_delivery_out/release_reject_out` 双结构。
2. `bound_skills` 与 `participating_processes` 可映射到 M3 主流程阶段。
3. Fail-Closed 路径可直接转写为运行级测试用例。
4. 生命周期状态保持 `draft`，不宣称运行可用。

