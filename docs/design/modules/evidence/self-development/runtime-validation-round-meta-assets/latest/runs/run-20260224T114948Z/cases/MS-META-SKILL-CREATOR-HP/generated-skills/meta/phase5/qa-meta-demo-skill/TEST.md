# qa-meta-demo-skill - Test Cases

## Objective Alignment

验证 `qa-meta-demo-skill` 的能力定义满足可执行、可测试与可追溯要求。

## Test Cases

### TC-001: Happy Path - 主链路通过

- Type: Objective
- Priority: P0
- Input: 合法输入
- Expected: 产出满足 output_contract
- Evaluation Method: Exact Match

### TC-002: Fail-Closed - 缺失关键输入

- Type: Objective
- Priority: P0
- Input: 缺失 required 字段
- Expected: 阻断并返回缺失字段
- Evaluation Method: Exact Match

### TC-003: Fail-Closed - 约束冲突

- Type: Objective
- Priority: P0
- Input: 构造约束冲突输入
- Expected: 阻断并返回冲突原因
- Evaluation Method: Rule Match

### TC-004: Traceability - 输入输出映射

- Type: Objective
- Priority: P1
- Input: 合法输入
- Expected: 输出字段可回链到输入与契约
- Evaluation Method: Rule Match

### TC-005: 异常路径恢复

- Type: Objective
- Priority: P1
- Input: 部分可恢复异常
- Expected: 输出恢复/回退建议
- Evaluation Method: Human Review

### TC-006: 文档门禁一致性

- Type: Objective
- Priority: P2
- Input: 完整执行结果
- Expected: test_mount、registry tests 与文档一致
- Evaluation Method: Rule Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 1
- Judge Perspectives: [architect, qa]
- Timeout Seconds: 600
- Retry Policy: max 1
