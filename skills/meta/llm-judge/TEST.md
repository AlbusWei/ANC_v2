# llm-judge - Test Cases

## Objective Alignment

验证评判输出结构完整、可追溯、可用于门禁判定，并对关键输入缺失执行 Fail-Closed。

## Test Cases

### TC-001: Happy Path - 返回结构化 verdict

- Type: Objective
- Priority: P0
- Input: 完整 `objective/spec_ref/expected_conditions/actual_output_ref`
- Expected: 输出含 `pass/confidence/remarks/suggestions/traceability`
- Evaluation Method: Exact Match

### TC-002: Fail-Closed - 缺失 actual_output_ref

- Type: Objective
- Priority: P0
- Input: `actual_output_ref` 缺失
- Expected: 返回失败决策，禁止给出通过结论
- Evaluation Method: Exact Match

### TC-003: Fail-Closed - expected_conditions 为空

- Type: Objective
- Priority: P0
- Input: `expected_conditions=[]`
- Expected: 返回码为 2，标记输入不可判定
- Evaluation Method: Exact Match

### TC-004: Traceability - 结论可回链证据

- Type: Objective
- Priority: P1
- Input: 正常输入
- Expected: `traceability` 包含 `spec_ref` 与 `actual_output_ref` 映射
- Evaluation Method: Rule Match

### TC-005: 置信度范围检查

- Type: Objective
- Priority: P1
- Input: 正常输入
- Expected: `confidence` 在 `[0,1]` 区间
- Evaluation Method: Exact Match

### TC-006: 失败建议可执行性

- Type: Objective
- Priority: P2
- Input: 会触发 fail 的输出
- Expected: `suggestions` 至少 1 条且可执行
- Evaluation Method: Human Review

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 1
- Judge Perspectives: [qa, architect]
- Timeout Seconds: 600
- Retry Policy: max 1
