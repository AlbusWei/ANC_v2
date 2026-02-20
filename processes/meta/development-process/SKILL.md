---
name: "development-process"
description: "Minimum process for Objective->Spec->Test->Implement->Verify loop"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# development-process

## Objective

提供 ANC v2 第一条可运行的元流程闭环，验证因果驱动链的执行可行性。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: admin, architect, hr, kernel-dev
- Priority support: P0 / P1 / P2

## Input Contract

- Format: json
- Required fields: objective_ref, input_payload, test_case_ref

## Output Contract

- Format: json
- Required fields: final_output, evidence_refs, verdict, fail_closed

## Runtime Rules

1. 必须经 BPM 调度。
2. Phase 执行必须满足 SIPOC 与验收条件。
3. `p4` Verify 阶段默认后端为 `scenario_python`，并由 `llm-judge` 归一化输出 ANC verdict。
4. 门禁仅接受标准化 verdict，不直接消费 Scenario 原始结果。
5. 缺证据或校验失败时 Fail-Closed。
