# AP-036 Construction Round Close Verification

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: system.ops.manual-task
- Input:
  - round_id
  - m6_update_bundle_ref
  - superpower_sync_ref
  - round_evidence_log_ref
  - open_questions_ref
- Output:
  - registry_verify_report_ref
  - round_close_summary_ref
- Fail-Closed:
  - `registry_contract_tool.py verify` 失败
  - `registry_contract_tool.py verify-m6 --round-dir <round-dir>` 失败
  - 回合日志缺失 round_open 或 round_close 事件
  - 任一提交缺失 Entire-Checkpoint
- Evidence:
  - registry_verify_report_ref
  - round_close_summary_ref
