# AP-021 Hold Progress Evidence Collection

> 版本: v0.2.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.hold-triage
- Input:
  - hold_case_ref
  - runtime_log_ref
  - execution_state_ref
  - liveness_policy_ref
  - no_progress_window_ref
- Output:
  - progress_signals_ref
  - progress_evidence_ref
  - no_progress_duration_seconds
- Minimum signals:
  - 日志增量
  - 阶段状态推进
  - 输出流心跳
  - 会话活性更新时间推进
- Fail-Closed:
  - 三类信号缺失且无法补证 -> `fail`
  - evidence 索引不可追溯 -> `fail`
  - no_progress_window 小于 900 秒或缺失 -> `fail`
- Evidence:
  - progress_evidence_ref
