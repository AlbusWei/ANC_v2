# test-designer - Test Cases

## Objective Alignment

对齐 `obj-phase1-min-loop`，验证测试设计是否覆盖 Objective 核心意图。

## Test Cases

### TC-001: Objective 覆盖

- Type: Objective
- Priority: P0
- Input: objective_ref + spec_ref
- Expected: 每个关键 Spec 至少对应一个 test case
- Evaluation Method: Human Review

### TC-002: P0 风险场景

- Type: Objective
- Priority: P0
- Input: risk_focus
- Expected: 输出中至少包含一个 P0 风险测试场景
- Evaluation Method: Human Review

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
