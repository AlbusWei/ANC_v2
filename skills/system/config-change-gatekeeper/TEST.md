# config-change-gatekeeper - Test Cases

## Objective Alignment

验证配置变更门禁校验在证据不足时能够 fail-closed。

## Test Cases

### TC-001: 证据完整通过门禁

- Type: Objective
- Priority: P0
- Input: 完整 change_request + rollback_plan + evidence_refs
- Expected: 输出 `approval/risk_level/gate_report_ref`
- Evaluation Method: Exact Match

### TC-002: 缺证据拒绝流转

- Type: Objective
- Priority: P0
- Input: `evidence_refs` 为空
- Expected: `approval=deny` 且给出拒绝原因
- Evaluation Method: Exact Match
