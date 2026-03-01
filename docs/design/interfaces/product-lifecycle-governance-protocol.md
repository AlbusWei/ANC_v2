# Product Lifecycle Governance Protocol

## 协议目标

定义以 `Product` 为治理语义中心、以 `ProductVersionInstance` 为生命周期对象的统一治理接口，确保版本实例迁移、角色切换、演化提案接入具备一致输入输出与 fail-closed 约束。

## 协议对象

1. `Product`
2. `ProductVersionInstance`
3. `VersionRoleTag`
4. `EvolutionProposal`

## 通用约束

1. `Product` 必须具备：`goal`、`consumer`、`scope`、`acceptance`、`version_policy`。
2. `ProductVersionInstance` 主键：`product_id + branch_or_worktree_id`。
3. 状态迁移与角色切换必须携带证据引用（验证、风险、回滚）。
4. 证据缺失、指标不可比、回滚缺失时 fail-closed。

## 关键接口

### 1) create_product

- 输入：`product_id`、`goal`、`consumer`、`scope`、`acceptance`、`version_policy`
- 输出：`product_ref`
- 失败：任一必填缺失则拒绝创建

### 2) create_version_instance

- 输入：`product_id`、`branch_or_worktree_id`、`initial_state`、`role_tag`、`asset_bindings`
- 输出：`version_instance_ref`
- 失败：`product_id` 不存在或绑定不完整则拒绝

### 3) transition_version_state

- 输入：`version_instance_ref`、`from_state`、`to_state`、`evidence_refs`
- 输出：`transition_record_ref`
- 失败：非法迁移或证据不足则拒绝

### 4) switch_version_role

- 输入：`version_instance_ref`、`from_role`、`to_role`、`verification_ref`、`risk_assessment_ref`、`rollback_plan_ref`
- 输出：`role_switch_record_ref`
- 失败：缺少任一治理证据则拒绝

### 5) submit_evolution_proposal

- 输入：`proposal_id`、`trigger_type`、`target_product_id`、`expected_value`、`verification_metrics`、`rollback_plan`
- 输出：`evolution_proposal_ref`
- 失败：目标产品不存在、指标不可比较或回滚未定义

## 协作边界

1. M5 产出演化提案并调用 `submit_evolution_proposal`。
2. M3 消费提案并实施变更，不负责治理放行。
3. M1 产出验证证据，作为 M4 状态/角色迁移输入。
4. M4 执行 `transition_version_state` 与 `switch_version_role`，完成放行。
