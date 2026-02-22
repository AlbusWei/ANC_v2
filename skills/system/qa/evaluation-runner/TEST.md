# evaluation-runner - Test Cases

## Objective Alignment

验证 `quality_eval_runner` 在三类评测模式下输出统一 verdict 与证据路径。

## Test Cases

### TC-001: Happy Path - objective 模式执行成功

- Type: Objective
- Priority: P0
- Input: 合法 `preparation_bundle_ref` + `actual_output_refs`
- Expected: 返回 `evaluation_verdict=pass` 且包含 `raw_eval_ref`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [evaluation_verdict, gate_decision, raw_eval_ref, execution_state_ref]

### TC-002: Fail-Closed - 无效 mode 拒绝执行

- Type: Objective
- Priority: P0
- Input: `evaluation_mode=unknown`
- Expected: `gate_decision=fail` 或 `test_invalid`，并保留 runner 错误
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=test_invalid, contract_error]

### TC-003: Traceability - 输出证据索引完整

- Type: Objective
- Priority: P0
- Input: 合法 objective/regression 运行输入
- Expected: `runner_log_ref`、`execution_state_ref`、`evidence_ref` 均可追溯
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [runner_log_ref, execution_state_ref, evidence_ref]

### TC-004: LLM Judge Fail-Closed - 缺失密钥

- Type: Objective
- Priority: P0
- Input: `Evaluation Method=LLM-Judge` 且环境缺失 `OPENAI_API_KEY`
- Expected: `gate_decision=test_invalid`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=test_invalid, missing_judge_api_key_env]

### TC-005: LLM Judge Fail-Closed - 模型不受支持

- Type: Objective
- Priority: P0
- Input: `Evaluation Method=LLM-Judge` + `judge_model=GPT-5.2`，provider/account 不支持该模型
- Expected: `gate_decision=test_invalid`，错误原因含 `judge_model_unsupported`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=test_invalid, judge_model_unsupported]

### TC-006: LLM Judge Dynamic Grader Plan

- Type: Objective
- Priority: P0
- Input: `Evaluation Method=LLM-Judge` + `grader_selection/grader_weights`
- Expected: runner 根据测试计划动态选择 grader 并输出 grader 级结果
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [selected_graders, graders, overall_normalized_score]

### TC-007: Subjective Blind A/B Traceability

- Type: Objective
- Priority: P0
- Input: `mode=subjective` + baseline/candidate outputs + seed/rounds
- Expected: `comparisons[]` 含 `blind_assignment` 与 `judge_result`，并可复现
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [comparisons, blind_assignment, judge_result, seed, rounds]

### TC-008: Fail-Closed - 缺失 actual_output_refs

- Type: Objective
- Priority: P0
- Input: 合法 `preparation_bundle_ref` 但不传 `--actual-output`
- Expected: `gate_decision=test_invalid` 且 reasons 包含 `missing_actual_output`
- Evaluation Method: Rule Match
- Judge Payload:
  - expected_conditions: [gate_decision=test_invalid, missing_actual_output]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
