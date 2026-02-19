# spec-writer - Test Cases

## Objective Alignment

对齐 `obj-phase1-min-loop`，验证 spec 输出满足可执行约束。

## Test Cases

### TC-001: 必要章节完整性

- Type: Objective
- Priority: P0
- Input: objective_ref + problem_statement + constraints
- Expected: 产出含 scope/input_contract/output_contract/acceptance_criteria/risks
- Evaluation Method: Human Review

### TC-002: 可验证约束检查

- Type: Objective
- Priority: P0
- Input: 同 TC-001
- Expected: 不含无法验证的空泛描述
- Evaluation Method: Human Review

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [architect]
- Timeout Seconds: 600
- Retry Policy: max 1
