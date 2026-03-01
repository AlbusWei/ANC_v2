# test-designer - Test Cases

## Objective Alignment

验证测试设计覆盖 Objective 与 Spec 的关键约束，且输出可直接进入执行与门禁流程。

## Test Cases

### TC-001: Happy Path - 关键条款全覆盖

- Type: Objective
- Priority: P0
- Input: 合法 `objective_ref/spec_ref/risk_focus`
- Expected: 每条关键 Spec 至少有 1 个对应测试用例
- Evaluation Method: Human Review

### TC-002: Fail-Closed - 缺失 spec_ref

- Type: Objective
- Priority: P0
- Input: `spec_ref` 缺失
- Expected: 阻断并返回缺失引用
- Evaluation Method: Rule Match

### TC-003: Fail-Closed - risk_focus 无 P0 场景

- Type: Objective
- Priority: P0
- Input: `risk_focus` 仅含 P1/P2
- Expected: 阻断并提示补齐 P0 场景
- Evaluation Method: Rule Match

### TC-004: Traceability - test_cases 映射 spec 条款

- Type: Objective
- Priority: P1
- Input: 含多条 Spec 约束
- Expected: 输出 traceability_map 可逐条回链
- Evaluation Method: Human Review

### TC-005: Evaluation 配置可执行性

- Type: Objective
- Priority: P1
- Input: 标准输入
- Expected: `evaluation_config` 至少包含轮次/视角/超时
- Evaluation Method: Exact Match

### TC-006: 负向可恢复性 - 异常路径可回退

- Type: Objective
- Priority: P2
- Input: 含异常链路需求
- Expected: 用例中明确回退步骤与恢复判定
- Evaluation Method: Human Review

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 1
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
