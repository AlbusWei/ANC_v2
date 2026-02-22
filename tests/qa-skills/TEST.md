# qa-skills-round5 - Test Cases

## Objective Alignment

补测 `sys.qa.*` 七个新开发技能在真实脚本执行下的有效性、Fail-Closed 行为与证据可追溯性。

## Test Cases

### TC-001: test-compiler 编译成功

- Type: Objective
- Priority: P0
- Input: `TEST_rule.md` + baseline profile
- Expected: `gate_decision=pass` 且产出 datapoints/map/report
- Evaluation Method: Rule Match

### TC-002: test-compiler 空 profile_set Fail-Closed

- Type: Objective
- Priority: P0
- Input: `profile_set=""`
- Expected: `gate_decision=test_invalid`
- Evaluation Method: Rule Match

### TC-003: evaluation-runner objective 成功

- Type: Objective
- Priority: P0
- Input: preparation bundle + pass output
- Expected: `gate_decision=pass` 且有 `raw_eval_ref`
- Evaluation Method: Rule Match

### TC-004: evaluation-runner 缺失 actual-output Fail-Closed

- Type: Objective
- Priority: P0
- Input: objective mode without `--actual-output`
- Expected: `gate_decision=test_invalid`
- Evaluation Method: Rule Match

### TC-005: verdict-normalizer pass 聚合

- Type: Objective
- Priority: P0
- Input: objective=pass + regression=pass
- Expected: `gate_decision=pass`
- Evaluation Method: Rule Match

### TC-006: verdict-normalizer test_invalid 聚合透传

- Type: Objective
- Priority: P0
- Input: objective=test_invalid + regression=pass
- Expected: `gate_decision=test_invalid`
- Evaluation Method: Rule Match

### TC-007: hold-triage policy 冲突时 Fail-Closed

- Type: Objective
- Priority: P0
- Input: 无进展信号 + 不允许动作 policy
- Expected: `triage_action=fail` + `gate_decision=fail`
- Evaluation Method: Rule Match

### TC-008: regression-runner 跨模块回归通过

- Type: Objective
- Priority: P0
- Input: scope=M3,M4 + pass output
- Expected: `release_gate_candidate=pass`
- Evaluation Method: Rule Match

### TC-009: regression-runner 输出映射歧义 Fail-Closed

- Type: Objective
- Priority: P0
- Input: scope=M3,M4,M5 + 2 outputs
- Expected: `release_gate_candidate=fail`
- Evaluation Method: Rule Match

### TC-010: registry-validator verify 通过

- Type: Objective
- Priority: P0
- Input: 有效 registry tool
- Expected: `gate_decision=pass`
- Evaluation Method: Rule Match

### TC-011: registry-validator tool 缺失 Fail-Closed

- Type: Objective
- Priority: P0
- Input: 不存在的 `registry_tool_ref`
- Expected: `gate_decision=fail`
- Evaluation Method: Rule Match

### TC-012: evidence-archiver 归档成功

- Type: Objective
- Priority: P0
- Input: 合法元数据 + traceability refs
- Expected: `gate_decision=pass` 且产出 index/report
- Evaluation Method: Rule Match

### TC-013: evidence-archiver 缺失 traceability 输入 Fail-Closed

- Type: Objective
- Priority: P0
- Input: 不传 `input_ref` 且不传 `raw_eval_ref`
- Expected: `gate_decision=fail`
- Evaluation Method: Rule Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 900
- Retry Policy: max 1
