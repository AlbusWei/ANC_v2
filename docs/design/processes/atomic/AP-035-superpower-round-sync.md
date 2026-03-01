# AP-035 Superpower Round Sync

> 版本: v1.0.0 | 层级: P6 | 类型: 原子流程

- Actor: architect
- Skill: system.integration.superpower-sync
- Input:
  - round_id
  - round_goal
  - superpower_ref
  - anc_design_refs
  - decision_snapshot_ref
  - sync_actor
  - trigger_mode
  - risk_level
  - checkpoint_count
  - commit_count
  - round_evidence_log_ref
  - output_ref
- Output:
  - superpower_sync_ref
  - sync_status
  - validate_report_ref
  - status_report_ref
- Fail-Closed:
  - 输出记录不满足 Superpower 协同 schema
  - checkpoint_count 与 commit_count 不一致
  - round_id 与 superpower_ref 绑定关系冲突
- Evidence:
  - superpower_sync_ref
