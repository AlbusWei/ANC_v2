---
name: "llm-judge"
description: "Evaluate outputs against objective/spec and return structured verdict"
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

为 ANC 的测试门禁提供客观/主观评估能力，输出可执行反馈。

## Input Contract

- Format: json
- Required fields: objective, spec_ref, expected_conditions, actual_output_ref

## Output Contract

- Format: json
- Required fields: pass, confidence, remarks, suggestions

## Behavior Specification

1. 读取 `spec_ref` 和 `actual_output_ref`。
2. 基于 `objective` 与 `expected_conditions` 进行判定。
3. 输出结构化 verdict，失败时必须给出具体改进建议。

## Constraints

- 不得仅依据关键词匹配给出通过结论。
- 缺关键输入时必须 Fail-Closed。

## Version

- Current: 0.1.0
- Status: Draft
