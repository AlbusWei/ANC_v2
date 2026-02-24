# process-creator - Test Cases

## Objective Alignment

验证流程资产生成满足连续性约束、phase 闭合约束和断点处理规则，并能在违规时 Fail-Closed。

## Test Cases

### TC-001: Happy Path - 生成可校验流程三件套

- Type: Objective
- Priority: P0
- Input: 合法 `process_id/version/process_level/phases/control_flow/fail_policy/evidence_policy/lineage_policy`
- Expected: 输出 `process_manifest_path/process_skill_path/process_guide_path`，并可通过 registry verify
- Evaluation Method: Exact Match

### TC-002: Fail-Closed - phase 缺 target_id

- Type: Objective
- Priority: P0
- Input: 某 phase 缺 `target_id`
- Expected: 返回 phase 闭合错误，返回码为 2
- Evaluation Method: Exact Match

### TC-003: Fail-Closed - requires_spec=true 但无 spec_ref

- Type: Objective
- Priority: P0
- Input: phase 标记 `requires_spec=true` 且无 `spec_ref`
- Expected: 阻断生成并报告缺失字段
- Evaluation Method: Exact Match

### TC-004: Traceability - phase 到 AP/子流程映射

- Type: Objective
- Priority: P1
- Input: 多 phase 输入
- Expected: 每个 phase 都能映射到 `target_type/target_id`，未注册 target 必须提供合法 `inline_ap`
- Evaluation Method: Rule Match

### TC-005: 连续性约束检查 - 跨非连续生命周期段

- Type: Objective
- Priority: P1
- Input: phase 顺序跨段拼接
- Expected: 返回 continuity violation
- Evaluation Method: Exact Match

### TC-006: 报告输出检查 - 包含失败决策原因

- Type: Objective
- Priority: P2
- Input: 触发 Fail-Closed 的输入 + `--report`
- Expected: 报告含 `decision=fail_closed` 与违规 phase 清单
- Evaluation Method: Exact Match

### TC-007: Fail-Closed - P4 缺协作策略

- Type: Objective
- Priority: P0
- Input: `process_level=P4` 且缺 `collaboration_policy`
- Expected: 阻断生成并返回 `collaboration_policy:required_for_p4`
- Evaluation Method: Exact Match

### TC-008: Fail-Closed - 多 Actor 的 P5 缺协作策略

- Type: Objective
- Priority: P1
- Input: `process_level=P5` 且 phase 存在多个 actor，但缺 `collaboration_policy`
- Expected: 阻断生成并返回 `collaboration_policy:required_for_multi_actor_p5_p6`
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [architect, bpm]
- Timeout Seconds: 600
- Retry Policy: max 1
