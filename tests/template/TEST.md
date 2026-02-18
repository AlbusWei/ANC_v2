# [Skill Name] - Test Cases

## Objective Alignment

[这些用例验证哪个 Objective]

## Test Cases

### TC-001: [场景名]

- Type: Objective / Subjective
- Priority: P0 / P1 / P2
- Input: [具体输入]
- Expected: [预期结果]
- Evaluation Method: LLM-Judge / Human Review / Exact Match
- Judge Payload:
  - objective: [目标描述]
  - spec_ref: [规范路径]
  - expected_conditions: [验收条件列表]
  - actual_output_ref: [实际输出路径]

### TC-002: [场景名]

- Type: Objective / Subjective
- Priority: P0 / P1 / P2
- Input: [具体输入]
- Expected: [预期结果]
- Evaluation Method: LLM-Judge / Human Review / Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 9
- Judge Perspectives: [default / role list]
- Timeout Seconds: 600
- Retry Policy: max 1
