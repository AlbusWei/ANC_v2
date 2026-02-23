# objective-writer - Test Cases

## Objective Alignment

验证 Objective 文档产出满足“可测、可追溯、边界清晰”的准入要求，且对关键输入缺失执行 Fail-Closed。

## Test Cases

### TC-001: Happy Path - 产出可测 Objective

- Type: Objective
- Priority: P0
- Input: 完整 `objective_context/stakeholders/constraints/success_criteria`
- Expected: 输出包含 `objective_ref/objective_statement/scope_baseline/non_goals`
- Evaluation Method: Human Review

### TC-002: Fail-Closed - 缺失 success_criteria

- Type: Objective
- Priority: P0
- Input: `success_criteria=[]`
- Expected: 阻断产出并明确“成功标准不可测”
- Evaluation Method: Rule Match

### TC-003: Fail-Closed - 缺失 non_goals

- Type: Objective
- Priority: P0
- Input: `constraints` 不含 `non_goals`
- Expected: 阻断产出并返回缺失边界说明
- Evaluation Method: Rule Match

### TC-004: Traceability - 输出条款映射输入约束

- Type: Objective
- Priority: P1
- Input: 含多条约束的完整输入
- Expected: `scope_baseline` 与输入约束逐条可追溯
- Evaluation Method: Human Review

### TC-005: 冲突检查 - 目标与 SSOT 冲突

- Type: Objective
- Priority: P1
- Input: 明确冲突的约束描述
- Expected: 标记 `ssot_conflict` 并拒绝进入下一阶段
- Evaluation Method: Rule Match

### TC-006: 可用性检查 - 输出可直接进入 Spec 阶段

- Type: Objective
- Priority: P2
- Input: 标准完整输入
- Expected: Spec-writer 无需补充解释即可消费
- Evaluation Method: Human Review

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 1
- Judge Perspectives: [architect, system-analyst]
- Timeout Seconds: 600
- Retry Policy: max 1
