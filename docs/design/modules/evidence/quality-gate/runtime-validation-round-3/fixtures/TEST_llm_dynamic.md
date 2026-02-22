# qa-runtime-llm-dynamic - Test Cases

## Objective Alignment

验证 LLM-as-Judge 可按测试计划动态选择 grader，并输出结构化 grader 结果。

## Test Cases

### TC-001: Dynamic Grader Plan

- Type: Objective
- Priority: P0
- Input: objective/spec/actual_output_ref
- Expected: output aligns objective and keeps traceability
- Evaluation Method: LLM-Judge
- Judge Payload:
  - objective: verify objective-spec-output alignment and traceability
  - context: spec requires gate_decision, evidence_ref, reasons
  - expected_conditions: [gate_decision, evidence_ref, reasons]
  - grader_selection: [relevance, correctness, instruction_following]
  - grader_weights: {"relevance":0.4,"correctness":0.4,"instruction_following":0.2}
  - min_score_per_grader: {"relevance":3,"correctness":3,"instruction_following":3}
  - must_pass_graders: [relevance, correctness]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
