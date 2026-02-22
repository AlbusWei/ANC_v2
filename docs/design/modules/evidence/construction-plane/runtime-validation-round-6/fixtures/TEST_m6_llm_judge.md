# m6-llm-regression - Test Cases

## Objective Alignment

验证 M6 运行结果可进入 LLM-as-Judge 评测通道，并在无效模型时 Fail-Closed。

## Test Cases

### TC-001: M6 结果 LLM 评测契约

- Type: Objective
- Priority: P0
- Input: objective/spec/actual_output_ref
- Expected: round result reports status=passed and includes full p1-p5 completion trace
- Evaluation Method: LLM-Judge
- Judge Payload:
  - objective: verify the M6 round result represents a successfully closed governance round
  - expected_conditions: [phase closure is traceable, fail closed conditions are explicit, evidence references are present]
  - reference_response: round result is passed, p1 to p5 are completed, and output_ref is present
  - grader_selection: [relevance]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Grader Selection: [relevance]
- Timeout Seconds: 600
- Retry Policy: max 1
