# test-compiler - Test Cases

## Objective Alignment

验证 `TEST.md -> datapoints` 编译链路满足 M1 统一门禁准备要求。

## Test Cases

### TC-001: Happy Path - 编译成功并输出映射

- Type: Objective
- Priority: P0
- Input: 合法 `TEST.md` + baseline profile
- Expected: 产出 `test_datapoints_ref/tc_profile_map_ref/compile_report_ref`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [test_datapoints_ref, tc_profile_map_ref, compile_report_ref, gate_decision]

### TC-002: Fail-Closed - 模板错误触发 test_invalid

- Type: Objective
- Priority: P0
- Input: 缺少 `## Test Cases` 或 `TC-*` 的 `TEST.md`
- Expected: `gate_decision=test_invalid` 且 compile_report 记录 parse_error
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=test_invalid, parse_error]

### TC-003: Traceability - 证据链可追溯

- Type: Objective
- Priority: P0
- Input: 合法 `TEST.md`
- Expected: 输出中包含可达 `evidence_ref`，且 `test_mount` 与 registry tests 一致
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [evidence_ref, test_mount, methodology_ref]

### TC-004: Fail-Closed - profile_set 为空

- Type: Objective
- Priority: P0
- Input: `profile_set` 传空字符串
- Expected: `gate_decision=test_invalid` 且 compile_report 记录 `empty_profile_set`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=test_invalid, empty_profile_set]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
