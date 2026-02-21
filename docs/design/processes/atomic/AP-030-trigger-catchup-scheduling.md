# AP-030 Trigger Catchup Scheduling

> 版本: v0.2.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: sys.bpm.catchup-scheduler
- Input:
  - missed_run_ref
  - catchup_policy_ref
  - trigger_policy_ref
  - runtime_state_ref
- Output:
  - catchup_decision
  - catchup_run_ref
  - escalation_hint
  - computed_window_ref
- Fail-Closed:
  - 漏跑证据缺失 -> `fail`
  - 动态窗口不可计算 -> `fail`
  - 补跑决策不确定 -> `fail`
- Evidence:
  - catchup_run_ref
  - catchup_reason_ref
  - computed_window_ref
