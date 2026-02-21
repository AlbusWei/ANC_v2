---
name: "test-designer"
description: "Design objective-aligned test cases before implementation"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# test-designer

## Objective

基于 Objective 与 Spec 设计先行测试用例，为 TDD 阶段提供准入门禁。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-phase1-min-loop
input_contract:
  format: json
  required:
    - objective_ref
    - spec_ref
    - risk_focus
  validation:
    - objective_ref must be provided
    - spec_ref must point to an existing spec
    - risk_focus must include at least one P0 scenario
output_contract:
  format: markdown
  required:
    - objective_alignment
    - test_cases
    - evaluation_config
  machine_judgement:
    - each critical spec clause has at least one test case
    - output includes explicit P0 test scenarios
    - evaluation method is executable
fail_closed_rules:
  - missing objective_ref or spec_ref
  - no P0 risk scenario in output
  - output cannot be mapped to test template
test_mount:
  test_doc: /Users/albus/MyProjects/ANC_v2/skills/meta/test-designer/TEST.md
  methodology_ref: /Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md
```

## Input Contract

- Format: json
- Required fields: objective_ref, spec_ref, risk_focus

## Output Contract

- Format: markdown
- Required fields: objective_alignment, test_cases, evaluation_config

## Behavior Specification

1. 覆盖 Objective 核心意图，不仅覆盖格式要求。
2. 每条关键 Spec 至少对应一个 test case。
3. 输出包含优先级和评估方法。

## Constraints

- 不得将实现细节写入测试前置阶段。
- 不得遗漏 P0 风险场景。

## Version

- Current: 0.1.0
- Status: Draft
