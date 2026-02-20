# llm-judge - Test Cases

## Objective Alignment

对齐 `obj-phase1-min-loop`，验证 Scenario 执行 + ANC 归一化 + Fail-Closed 门禁链。

## Test Cases

### TC-SCN-001: Objective 正常通过

- Type: Objective
- Priority: P0
- Input:
  - objective/spec_ref/expected_conditions/actual_output_ref/test_case_ref
  - evaluation_mode: `objective`
  - backend: `scenario_python`
- Expected:
  - 返回 `pass/confidence/remarks/suggestions/evidence_refs`
  - `fail_closed=false`
- Evaluation Method: LLM-Judge + Contract Check

### TC-SCN-002: 缺失输入 Fail-Closed

- Type: Objective
- Priority: P0
- Input: missing `actual_output_ref`
- Expected:
  - `fail_closed=true`
  - `fail_closed_reason` 包含 missing required input
- Evaluation Method: Exact Match

### TC-SCN-003: judge 结果不可解析

- Type: Objective
- Priority: P0
- Input: 注入不可解析 raw result
- Expected:
  - `fail_closed=true`
  - `pass=false`
- Evaluation Method: Exact Match

### TC-SCN-004: 执行超时

- Type: Objective
- Priority: P0
- Input: `timeout_seconds` 极小 + 长响应场景
- Expected:
  - `fail_closed=true`
  - `fail_closed_reason` 包含 timeout
- Evaluation Method: Exact Match

### TC-SCN-005: 证据缺失

- Type: Objective
- Priority: P0
- Input: 缺失 `scenario/raw_result.json` 或 `normalized_verdict.json`
- Expected:
  - `fail_closed=true`
  - 拒绝门禁流转
- Evaluation Method: Exact Match

### TC-SCN-006: messages 语义校验

- Type: Objective
- Priority: P0
- Input: tool-calling 场景
- Expected:
  - 证据可还原真实会话和工具调用
  - 不依赖 judge 内部 prompt 文本充当会话消息
- Evaluation Method: Human Review + Contract Check

### TC-SCN-007: 外部上报不可用

- Type: Objective
- Priority: P1
- Input: 模拟事件上报失败
- Expected:
  - 门禁裁决仍可完成
  - 本地证据链完整
- Evaluation Method: Human Review

### TC-SCN-008: Subjective A/B 9轮裁决

- Type: Subjective
- Priority: P0
- Input:
  - evaluation_mode: `subjective_ab`
  - subjective_config.rounds: 9
  - subjective_config.thresholds.accept: 0.67
  - subjective_config.thresholds.reject: 0.5
- Expected:
  - 返回胜率统计
  - 按阈值输出 accept/reject/human-review
- Evaluation Method: LLM-Judge + Statistical Check

### TC-SCN-009: p4 fail -> p3 retry 回环证据

- Type: Objective
- Priority: P0
- Input: 在 `development-process` 中触发一次 p4 失败
- Expected:
  - 触发 `p4 -> p3` 回环
  - 回环前后证据可追溯
- Evaluation Method: Process Replay

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 9
- Judge Perspectives: [default, user, technical, product]
- Timeout Seconds: 600
- Retry Policy: max 1
- Backend: scenario_python
