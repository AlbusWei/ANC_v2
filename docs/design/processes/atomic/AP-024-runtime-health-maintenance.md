# AP-024 Runtime Health Maintenance

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: sys.bpm.process-instance-manager
- Input:
  - hold_case_ref
  - action_execution_ref
  - runtime_health_policy_ref
- Output:
  - health_maintenance_ref
  - runtime_recovery_state
- Fail-Closed:
  - 健康检查失败且无法恢复 -> `fail`
  - 恢复动作无证据 -> `fail`
- Evidence:
  - health_maintenance_ref
