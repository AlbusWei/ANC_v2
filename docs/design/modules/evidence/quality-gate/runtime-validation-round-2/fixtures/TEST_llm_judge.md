# qa-runtime-llm-fixture - Test Cases

## Objective Alignment

验证 LLM-as-Judge 模式在缺失模型密钥时 Fail-Closed。

## Test Cases

### TC-001: LLM Judge Contract

- Type: Objective
- Priority: P0
- Input: objective/spec/actual_output_ref
- Expected: llm judge executes with model credentials
- Evaluation Method: LLM-Judge
- Judge Payload:
  - objective: validate objective-spec-output alignment
  - expected_conditions: [objective aligned, spec aligned, output traceable]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Timeout Seconds: 600
- Retry Policy: max 1
