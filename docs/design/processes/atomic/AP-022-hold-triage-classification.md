# AP-022 Hold Triage Classification

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.hold-triage
- Input:
  - hold_case_ref
  - progress_signals_ref
  - triage_policy_ref
- Output:
  - triage_action（`continue|retry|debug|fail`）
  - triage_report_ref
- Fail-Closed:
  - triage 无明确决策 -> `fail`
  - 策略校验失败 -> `fail`
- Evidence:
  - triage_report_ref
