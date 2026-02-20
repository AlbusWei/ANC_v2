---
name: "llm-judge"
description: "Run scenario-backed evaluation and normalize results into ANC gate verdict"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# llm-judge

## Objective

为 ANC 测试门禁提供客观/主观评估能力：调用 Scenario 执行仿真评估，并输出 ANC 标准化 verdict。

## Input Contract

- Format: json
- Schema: `/Users/albus/MyProjects/ANC_v2/skills/meta/llm-judge/schemas/llm_judge_input.schema.json`
- Required fields:
  - objective
  - spec_ref
  - expected_conditions
  - actual_output_ref
  - test_case_ref
  - evaluation_mode (`objective` | `subjective_ab`)
  - backend (`scenario_python`)
  - timeout_seconds
  - evidence_root
- Optional fields:
  - subjective_config.rounds
  - subjective_config.perspectives
  - subjective_config.thresholds.accept
  - subjective_config.thresholds.reject
  - scenario_overrides.max_turns
  - scenario_overrides.cache_key
  - scenario_overrides.set_id

## Output Contract

- Format: json
- Schema: `/Users/albus/MyProjects/ANC_v2/skills/meta/llm-judge/schemas/llm_judge_output.schema.json`
- Required fields:
  - pass
  - confidence
  - remarks
  - suggestions
  - evidence_refs
  - judge_backend
  - fail_closed
  - fail_closed_reason

## Behavior Specification

1. 校验输入契约，缺失关键字段时立即 Fail-Closed。
2. 读取 `spec_ref`、`actual_output_ref`、`test_case_ref` 并生成 Scenario 执行输入。
3. 当 `evaluation_mode=objective`：
   - 执行单轮 Scenario 评估并产出原始结果。
   - 归一化为 ANC verdict（`pass/confidence/remarks/suggestions`）。
4. 当 `evaluation_mode=subjective_ab`：
   - 对 A/B 结果进行盲测随机化映射（X/Y）。
   - 多轮评估（默认 N=9）并统计胜率。
   - 按阈值输出 `accept/reject/human-review` 建议。
5. 执行 `fail_closed_guard`：
   - 判定可解析性
   - 证据完整性
   - 超时与异常状态
6. 落盘证据到 `evidence_root`：
   - `scenario/transcript.json`
   - `scenario/raw_result.json`
   - `scenario/normalized_verdict.json`
   - `scenario/fail_closed_guard.json`
7. 仅输出 ANC 标准 verdict，禁止返回未经归一化的 Scenario 原始结构。

## Normalization Rules

1. `pass = success && unmet_criteria.length == 0`
2. `remarks = reasoning`
3. `suggestions = unmet_criteria -> actionable fixes`
4. `confidence = ANC confidence calculator`（非 Scenario 原生字段）
5. `evidence_refs` 使用绝对路径，至少包含 transcript/raw_result/normalized_verdict/guard_log

## Constraints

- 不得仅依据关键词匹配给出通过结论。
- 缺关键输入时必须 Fail-Closed。
- 外部可视化或事件上报失败不得阻塞门禁结果。
- 禁止在 ANC 流程中使用 Scenario pytest `--debug` 参数。
- 不直接信任 Scenario Python `ScenarioResult.messages` 作为完整证据来源，必须使用会话真实消息快照。

## Version

- Current: 0.2.0
- Status: Active (Phase 1)
