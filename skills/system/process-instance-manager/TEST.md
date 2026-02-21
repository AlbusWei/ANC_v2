# process-instance-manager - Test Cases

## Objective Alignment

验证流程实例健康维护在可恢复与不可恢复场景下均有明确输出。

## Test Cases

### TC-001: 可恢复场景

- Type: Objective
- Priority: P0
- Input: 合法健康策略与恢复动作
- Expected: 输出 `runtime_recovery_state=stabilized`
- Evaluation Method: Exact Match

### TC-002: 不可恢复触发 fail

- Type: Objective
- Priority: P0
- Input: 健康检查连续失败且无可执行恢复动作
- Expected: `runtime_recovery_state=failed`
- Evaluation Method: Rule Match
