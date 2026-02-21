# AP-021 Hold Progress Evidence Collection

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.hold-triage
- Input:
  - hold_case_ref
  - runtime_log_ref
  - execution_state_ref
- Output:
  - progress_signals_ref
  - progress_evidence_ref
- Minimum signals:
  - 日志增量
  - 阶段状态推进
  - 输出流心跳
- Fail-Closed:
  - 三类信号缺失且无法补证 -> `fail`
  - evidence 索引不可追溯 -> `fail`
- Evidence:
  - progress_evidence_ref
