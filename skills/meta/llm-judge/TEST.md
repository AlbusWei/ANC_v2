# llm-judge - Test Cases

## Objective Alignment

对齐 `obj-phase1-min-loop`，验证评估输出结构完整且可执行。

## Test Cases

### TC-001: 客观判定输出结构

- Type: Objective
- Priority: P0
- Input: objective/spec/expected_conditions/actual_output_ref
- Expected: 返回 `pass/confidence/remarks/suggestions`
- Evaluation Method: Human Review

### TC-002: 缺失输入 Fail-Closed

- Type: Objective
- Priority: P0
- Input: missing `actual_output_ref`
- Expected: 返回失败或拒绝执行，不产生通过结论
- Evaluation Method: Human Review

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [default]
- Timeout Seconds: 600
- Retry Policy: max 1
