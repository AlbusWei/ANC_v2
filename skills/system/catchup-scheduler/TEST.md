# catchup-scheduler - Test Cases

## Objective Alignment

验证补跑策略在动态窗口下执行、超窗升级，并保持可审计决策。

## Test Cases

### TC-001: 动态窗口内执行补跑

- Type: Objective
- Priority: P0
- Input: `expected_run_at` 落在动态计算窗口内
- Expected: `catchup_decision=run` 并产出 `catchup_run_ref`
- Evaluation Method: Exact Match

### TC-002: 动态窗口外触发升级建议

- Type: Objective
- Priority: P0
- Input: `expected_run_at` 超出动态计算窗口
- Expected: `catchup_decision=escalate` 并包含 `escalation_hint`
- Evaluation Method: Exact Match

### TC-003: 策略不可计算直接失败

- Type: Objective
- Priority: P0
- Input: `catchup_policy_ref` 缺失关键参数
- Expected: Fail-Closed 并写入策略错误证据
- Evaluation Method: Exact Match
