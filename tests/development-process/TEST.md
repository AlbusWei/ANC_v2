# development-process - Test Cases

## Objective Alignment

验证 `development-process(meta)` 是否能在最简链路中产出 Scenario 归一化门禁结果与可追溯证据链。

## Test Cases

### TC-001: 端到端最简链路

- Type: Objective
- Priority: P0
- Input:
  - process: `processes/meta/development-process`
  - objective_ref: `obj-phase0.5-development-process`
  - input_payload: 新建 `demo-skill` 并完成最小验证闭环
  - test_case_ref: `/Users/albus/MyProjects/ANC_v2/tests/development-process/TEST.md`
- Expected:
  - 四个 phase 均有输出证据
  - `p4` 产出 `normalized_verdict`，包含 `pass/confidence/remarks/suggestions`
  - `p4` 证据包含 `scenario/transcript.json/raw_result.json/fail_closed_guard.json`
- Evaluation Method: LLM-Judge
- Judge Payload:
  - objective: verify objective-spec-test-development chain integrity with scenario-backed verify gate
  - spec_ref: `/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/process.json`
  - expected_conditions:
    - all phases produce output refs
    - fail-closed rules are enforced
    - verify phase writes normalized verdict and scenario evidence
  - actual_output_ref: `artifacts/development-process/tc-001-output.md`

### TC-002: 缺失 test_case_ref

- Type: Objective
- Priority: P0
- Input:
  - process: `processes/meta/development-process`
  - objective_ref: `obj-phase0.5-development-process`
  - input_payload: 新建技能
- Expected:
  - 流程在输入校验阶段失败
  - 输出缺失字段说明
  - 不进入后续 phase
- Evaluation Method: Exact Match

### TC-003: p4 fail -> p3 retry

- Type: Objective
- Priority: P0
- Input:
  - process: `processes/meta/development-process`
  - objective_ref: `obj-phase1-min-loop`
  - input_payload: 构造一个会触发 Verify 失败的 candidate_output
  - test_case_ref: `/Users/albus/MyProjects/ANC_v2/tests/development-process/TEST.md`
- Expected:
  - 触发一次 `p4 -> p3` 回环
  - 回环前后均保留证据与 decision
- Evaluation Method: Process Replay

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 9
- Judge Perspectives: default
- Timeout Seconds: 600
- Retry Policy: max 1
