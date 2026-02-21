# escalation-handler - Test Cases

## Objective Alignment

验证 HOLD 关闭与升级路径符合固定升级链和证据要求。

## Test Cases

### TC-001: 正常关闭

- Type: Objective
- Priority: P0
- Input: triage_action=continue 且健康状态稳定
- Expected: `final_resolution=closed`
- Evaluation Method: Exact Match

### TC-002: 失败升级

- Type: Objective
- Priority: P0
- Input: triage_action=fail 且健康状态失败
- Expected: `final_resolution=escalated` 且包含 `escalation_ref`
- Evaluation Method: Rule Match
