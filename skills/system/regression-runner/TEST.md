# regression-runner - Test Cases

## Objective Alignment

验证回归执行对跨模块 P0 风险有一致阻断能力。

## Test Cases

### TC-001: 跨模块回归通过

- Type: Objective
- Priority: P0
- Input: M3/M4/M5 回归结果均 pass
- Expected: `release_gate_candidate=pass`
- Evaluation Method: Exact Match

### TC-002: 任一模块 P0 fail 阻断

- Type: Objective
- Priority: P0
- Input: 任一模块回归结果包含 P0 fail
- Expected: `release_gate_candidate=fail`
- Evaluation Method: Rule Match
