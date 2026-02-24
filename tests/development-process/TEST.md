# development-process - Test Cases

## Objective Alignment

验证 `development-process` 是否能稳定跑通“目标澄清 -> 规格编写 -> 测试准备 -> 实现 -> 门禁裁决”的最小开发闭环，并在关键输入缺失时 Fail-Closed。

## Test Cases

### TC-001: 最小开发闭环（Happy Path）

- Type: Objective
- Priority: P0
- Input:
  - process: `development-process`
  - objective_ref: `obj-phase1-min-loop`
  - objective_context_ref: 为 `system.skill.mock-a` 增加最小可执行 smoke 检查
- Expected:
  - 五个 phase 均产生可追溯输出引用
  - 产出 `spec_ref`、`test_plan_ref`、`implementation_ref`
  - 最终产生 `final_gate_verdict_ref`（包含 pass/fail 与证据）
- Evaluation Method: LLM-Judge
- Judge Payload:
  - objective: verify minimum development loop can hand off across roles
  - spec_ref: `processes/meta/development-process/process.json`
  - expected_conditions:
    - all phases produce output refs
    - gate verdict is explicit and explainable
    - handoff chain objective->spec->test->implementation->gate is intact
  - actual_output_ref: `artifacts/development-process/tc-001-output.md`

### TC-002: 缺失 objective_context_ref

- Type: Objective
- Priority: P0
- Input:
  - process: `development-process`
  - objective_ref: `obj-phase1-min-loop`
- Expected:
  - 流程在输入校验阶段失败
  - 返回缺失字段说明
  - 不进入后续 phase
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 5
- Judge Perspectives: default
- Timeout Seconds: 600
- Retry Policy: max 1
