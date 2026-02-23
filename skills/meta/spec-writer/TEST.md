# spec-writer - Test Cases

## Objective Alignment

验证 Spec 产出满足可执行、可测试、可回退三项核心要求，并在关键输入缺失时 Fail-Closed。

## Test Cases

### TC-001: Happy Path - 章节完整且可执行

- Type: Objective
- Priority: P0
- Input: 完整 `objective_ref/problem_statement/constraints`
- Expected: 包含 `scope/input_contract/output_contract/acceptance_criteria/risks/rollback_strategy`
- Evaluation Method: Human Review

### TC-002: Fail-Closed - 缺失 objective_ref

- Type: Objective
- Priority: P0
- Input: 缺失 `objective_ref`
- Expected: 阻断产出并报告缺失字段
- Evaluation Method: Rule Match

### TC-003: Fail-Closed - 验收条款不可测试

- Type: Objective
- Priority: P0
- Input: `acceptance_criteria` 含不可验证描述
- Expected: 返回 untestable criteria 并阻断
- Evaluation Method: Rule Match

### TC-004: Traceability - 条款映射 Objective

- Type: Objective
- Priority: P1
- Input: 含多条约束输入
- Expected: 每条验收条件都能追溯到 `objective_ref` 或输入约束
- Evaluation Method: Human Review

### TC-005: 风险回退检查 - rollback 可执行

- Type: Objective
- Priority: P1
- Input: 标准输入
- Expected: `rollback_strategy` 含触发条件、执行步骤和停止条件
- Evaluation Method: Human Review

### TC-006: SSOT 冲突检查

- Type: Objective
- Priority: P2
- Input: 与 SSOT 冲突的约束
- Expected: 标记冲突并拒绝进入开发阶段
- Evaluation Method: Rule Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 1
- Judge Perspectives: [architect, qa]
- Timeout Seconds: 600
- Retry Policy: max 1
