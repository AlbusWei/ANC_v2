# system-feedback-digest - Test Cases

## Objective Alignment

验证 `system-analyst` 在生产路径下具备 handoff 接收、结构化 digest 输出与 Fail-Closed 拒绝能力。

## Test Cases

### TC-SFD-001: 有效 handoff 生成 digest

- Type: Objective
- Priority: P0
- Input: 合法 handoff + 可达 evidence index
- Expected: `status=completed` 且输出 `architecture_feedback_digest_ref`
- Evaluation Method: Exact Match

### TC-SFD-002: 证据不足拒绝输出

- Type: Objective
- Priority: P0
- Input: evidence index 不可达或为空
- Expected: `status=rejected` 且输出 `reject_ref` 与 `reason_code=evidence_insufficient`
- Evaluation Method: Exact Match
