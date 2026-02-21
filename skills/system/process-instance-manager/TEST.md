# process-instance-manager - Test Cases

## Objective Alignment

验证 BPM 在实例创建、状态推进、递归隔离与流程闭合校验场景下满足 Fail-Closed 与证据可追溯要求。

## Test Cases

### TC-001: 创建实例并写入状态证据

- Type: Objective
- Priority: P0
- Input: 合法 `process_id + phase_id + lineage_ref`
- Expected: 产出 `instance_id/runtime_state/state_transition_ref/evidence_ref`
- Evaluation Method: Exact Match

### TC-002: 递归深度超限拒绝执行

- Type: Objective
- Priority: P0
- Input: `stack_depth` 超过流程 `lineage_policy.stack_depth_limit`
- Expected: Fail-Closed 并给出升级记录
- Evaluation Method: Exact Match

### TC-003: 流程闭合校验失败直接拒绝

- Type: Objective
- Priority: P0
- Input: manifest 中存在未映射 phase 或非法 control_flow
- Expected: Fail-Closed 并产出解析失败证据
- Evaluation Method: Exact Match
