# Release-Manager-Agent - USER

## 输入契约（release_request_in）

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

## 输出契约

### 成功输出（release_delivery_out）

1. `status`（`delivered`）
2. `request_id`
3. `release_package_ref`
4. `changelog_ref`
5. `release_decision`（`approved`）
6. `published_at`
7. `evidence_ref`

### 拒绝输出（release_reject_out）

1. `status`（`rejected`）
2. `request_id`
3. `reason_code`（`gate_failed|registry_invalid|rollback_unavailable|policy_conflict`）
4. `blocking_items`
5. `required_actions`
6. `evidence_ref`
