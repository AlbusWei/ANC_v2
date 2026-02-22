# template-skill - Test Cases

## Objective Alignment

验证模板技能可作为 ANC 标准化技能脚手架。

## Test Cases

### TC-001: Happy Path - 模板字段完整

- Type: Objective
- Priority: P0
- Input: `skills/template/SKILL.md`
- Expected: frontmatter 与 Capability Contract 字段齐全
- Evaluation Method: Exact Match

### TC-002: Fail-Closed - 缺失关键字段

- Type: Objective
- Priority: P0
- Input: 去掉 `test_mount` 或 `license`
- Expected: smoke 校验失败并给出缺失字段
- Evaluation Method: Exact Match

### TC-003: Traceability - 模板测试可追溯

- Type: Objective
- Priority: P0
- Input: 模板 + tests/template
- Expected: 输出可追溯测试路径与 methodology 引用
- Evaluation Method: Rule Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [architect]
- Timeout Seconds: 600
- Retry Policy: max 1
