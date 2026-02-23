# impact-analyzer - Test Cases

## Objective Alignment

验证变更影响分析在 happy path 下可输出完整契约字段，并在证据缺失/约束冲突时触发 Fail-Closed。

## Test Cases

### TC-IMPACT-HP: 合法输入输出 allow/hold/reject 之一

- Type: Objective
- Priority: P0
- Input: 可解析 proposal + 非空 scope + 可解析 risk constraints
- Expected: 输出 `impact_report_ref/risk_level/rollback_requirements/gating_recommendation`
- Evaluation Method: Exact Match

### TC-IMPACT-FC: scope 不可达或风险冲突未裁决

- Type: Objective
- Priority: P0
- Input: scope 路径不存在，或 risk 冲突且缺 adjudication
- Expected: Fail-Closed，门禁建议为 `hold` 或 `reject`
- Evaluation Method: Exact Match
