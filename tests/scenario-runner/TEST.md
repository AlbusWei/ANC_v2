# scenario-runner - Test Cases

## Objective Alignment

验证 `scenario-runner` 能稳定执行 Scenario 并产出完整原始证据链。

## Test Cases

### TC-RUN-001: Objective 单轮执行

- Type: Objective
- Priority: P0
- Input: objective/spec_ref/expected_conditions/actual_output_ref/evaluation_mode=objective
- Expected:
  - 返回 `success/transcript_ref/raw_result_ref`
  - 证据文件存在且可读取
- Evaluation Method: Exact Match

### TC-RUN-002: Subjective 多轮执行

- Type: Subjective
- Priority: P0
- Input: evaluation_mode=subjective_ab, rounds=9
- Expected:
  - 返回 9 轮运行元数据
  - 每轮 raw result 均有路径
- Evaluation Method: Exact Match

### TC-RUN-003: Timeout 返回

- Type: Objective
- Priority: P0
- Input: timeout_seconds 极小
- Expected:
  - `timeout=true`
  - 返回错误信息
- Evaluation Method: Exact Match

### TC-RUN-004: 外部事件不可用

- Type: Objective
- Priority: P1
- Input: 禁用/不可达事件上报
- Expected:
  - 本地 raw evidence 仍生成
  - 执行结果可返回
- Evaluation Method: Human Review

### TC-RUN-005: Evidence Root 不可写

- Type: Objective
- Priority: P0
- Input: evidence_root 指向不可写路径
- Expected:
  - 返回失败
  - 错误信息可定位
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 9
- Judge Perspectives: [default]
- Timeout Seconds: 600
- Retry Policy: max 1
