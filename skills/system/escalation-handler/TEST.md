# escalation-handler - Test Cases

## Objective Alignment

验证异常升级严格遵循治理链路，禁止越级与无证据升级。

## Test Cases

### TC-001: 正常升级到 admin

- Type: Objective
- Priority: P0
- Input: `incident_ref` 标记为高风险，链路完整
- Expected: 产出 `escalation_ref/escalation_trace/final_owner=admin`
- Evaluation Method: Exact Match

### TC-002: 越级请求被拒绝

- Type: Objective
- Priority: P0
- Input: 直接从 actor 跳过 bpm 请求 admin
- Expected: Fail-Closed 并写入拒绝证据
- Evaluation Method: Exact Match
