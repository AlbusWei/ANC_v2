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
