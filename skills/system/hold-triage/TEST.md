# hold-triage - Test Cases

## Objective Alignment

验证 HOLD 治理在长时运行场景下可产生可执行 triage 决策。

## Test Cases

### TC-001: 信号完整产生 triage

- Type: Objective
- Priority: P0
- Input: 三类进展信号齐全
- Expected: 返回 `triage_action` 与 `triage_report_ref`
- Evaluation Method: Exact Match

### TC-002: 信号缺失 fail-closed

- Type: Objective
- Priority: P0
- Input: 日志增量/阶段推进/心跳均缺失
- Expected: 返回 `triage_action=fail` 并升级
- Evaluation Method: Rule Match
