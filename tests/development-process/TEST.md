# development-process - Test Cases

## Objective Alignment

验证 `development-process` 是否能在最简链路中产出可追溯的 skill 资产与 registry 同步结果。

## Test Cases

### TC-001: 端到端最简链路

- Type: Objective
- Priority: P0
- Input:
  - process: `development-process`
  - objective_ref: `obj-phase0.5-development-process`
  - input_payload: 新建 `demo-skill`
  - target_skill_name: `demo-skill`
- Expected:
  - 四个 phase 均有输出证据
  - 生成 skill 与 test 资产
  - registry 更新草案包含正确路径
- Evaluation Method: LLM-Judge
- Judge Payload:
  - objective: verify objective-spec-test-development chain integrity
  - spec_ref: `/Users/albus/MyProjects/ANC_v2/processes/development-process/process.json`
  - expected_conditions:
    - all phases produce output refs
    - fail-closed rules are enforced
    - registry fields match generated assets
  - actual_output_ref: `artifacts/development-process/tc-001-output.md`

### TC-002: 缺失 target_skill_name

- Type: Objective
- Priority: P0
- Input:
  - process: `development-process`
  - objective_ref: `obj-phase0.5-development-process`
  - input_payload: 新建技能
- Expected:
  - 流程在输入校验阶段失败
  - 输出缺失字段说明
  - 不进入后续 phase
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 9
- Judge Perspectives: default
- Timeout Seconds: 600
- Retry Policy: max 1
