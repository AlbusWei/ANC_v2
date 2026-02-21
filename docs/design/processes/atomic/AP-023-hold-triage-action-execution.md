# AP-023 Hold Triage Action Execution

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.hold-triage
- Input:
  - hold_case_ref
  - triage_action
  - triage_report_ref
- Output:
  - action_execution_ref
  - hold_action_state
- Fail-Closed:
  - 执行动作与 triage 决策不一致 -> `fail`
  - `fail` 决策缺升级标记 -> `fail`
- Evidence:
  - action_execution_ref
