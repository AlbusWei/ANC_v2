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

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-phase1-min-loop
input_contract:
  format: json
  required:
    - objective
    - spec_ref
    - expected_conditions
    - actual_output_ref
  validation:
    - objective must be non-empty
    - spec_ref must be resolvable
    - expected_conditions must be a non-empty list
    - actual_output_ref must be resolvable
output_contract:
  format: json
  required:
    - pass
    - confidence
    - remarks
    - suggestions
  machine_judgement:
    - output must be valid json
    - pass must be boolean
    - confidence must be numeric
    - suggestions must be actionable when pass=false
fail_closed_rules:
  - missing critical input fields
  - actual_output_ref not resolvable
  - verdict payload cannot be parsed
test_mount:
  test_doc: /Users/albus/MyProjects/ANC_v2/skills/meta/llm-judge/TEST.md
  methodology_ref: /Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md
```

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
