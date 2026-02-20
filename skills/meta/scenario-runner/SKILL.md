---
name: "scenario-runner"
description: "Execute scenario-python simulations and persist raw evaluation evidence for ANC gate"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# scenario-runner

## Objective

作为 ANC 的测试执行底座，调用 Scenario Python SDK 执行仿真评估，并产出可回放的原始证据。

## Input Contract

- Format: json
- Required fields:
  - objective
  - spec_ref
  - expected_conditions
  - actual_output_ref
  - evaluation_mode (`objective` | `subjective_ab`)
  - timeout_seconds
  - evidence_root
- Optional fields:
  - rounds
  - perspectives
  - scenario.max_turns
  - scenario.cache_key
  - scenario.set_id

## Output Contract

- Format: json
- Required fields:
  - success
  - transcript_ref
  - raw_result_ref
  - run_metadata_ref
  - timeout
  - error

## Behavior Specification

1. 读取输入与被测输出，构造 Scenario 执行参数。
2. 执行 Scenario Python 仿真；objective 模式执行单轮，subjective_ab 支持多轮。
3. 将原始执行结果和会话快照落盘到 `evidence_root/scenario/`。
4. 输出仅包含执行结果与证据路径，不承担 ANC 门禁裁决。
5. 执行结束后返回结构化运行元数据（耗时、轮次、异常状态）。

## Constraints

- 不得输出 ANC 最终门禁 verdict（由 `llm-judge` 负责归一化）。
- 外部事件上报失败不得中断本地执行结果落盘。
- 超时必须返回 `timeout=true` 并附带错误信息。

## Version

- Current: 0.1.0
- Status: Active (Phase 1)
