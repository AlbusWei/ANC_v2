# AP-035 OpenSpec Round Sync

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: architect
- Skill: system.integration.openspec-sync
- Input:
  - round_id
  - round_goal
  - openspec_ref
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
  - openspec_sync_ref
  - sync_status
  - validate_report_ref
  - status_report_ref
- Fail-Closed:
  - 输出记录不满足 OpenSpec 协同 schema
  - checkpoint_count 与 commit_count 不一致
  - round_id 与 openspec_ref 绑定关系冲突
- Evidence:
  - openspec_sync_ref
