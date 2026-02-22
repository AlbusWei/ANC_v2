# hold-triage - Test Cases

## Objective Alignment

验证 HOLD 治理在活性检测与 Fail-Closed 上满足流程约束。

## Test Cases

### TC-001: Happy Path - 信号完整产出 continue/retry/debug

- Type: Objective
- Priority: P0
- Input: 日志增量+阶段推进+心跳齐全
- Expected: 返回合法 `triage_action` 与 triage 报告
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [triage_action, triage_report_ref, progress_signals_ref]

### TC-002: Fail-Closed - 无进展信号直接 fail

- Type: Objective
- Priority: P0
- Input: 三类信号均缺失
- Expected: `triage_action=fail` 且 `gate_decision=fail`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [triage_action=fail, gate_decision=fail]

### TC-003: Traceability - 输出证据链完整

- Type: Objective
- Priority: P0
- Input: 任一合法 hold_case
- Expected: `progress_signals_ref/triage_report_ref/action_execution_ref` 可追溯
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [progress_signals_ref, triage_report_ref, action_execution_ref]

### TC-004: Fail-Closed - policy 不允许动作时强制 fail

- Type: Objective
- Priority: P0
- Input: `on_no_progress=continue` 且 `allowed_actions` 不含 continue/debug/retry
- Expected: triage_action 被收敛到 `fail` 且 `gate_decision=fail`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [triage_action=fail, gate_decision=fail]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa, bpm]
- Timeout Seconds: 600
- Retry Policy: max 1
