---
name: "objective-scope-baseline"
description: "P5 子流程：按 AP-001/AP-002/AP-003 生成 objective 与 scope baseline"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.1.0"
---

# objective-scope-baseline

## Objective

将目标语义收敛与范围基线固化为可复用 P5 子流程，为 full-development/refactor 提供一致输入。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: architect, bpm
- Priority support: P1

## Input Contract

- Format: json
- Required fields: objective_context_ref

## Output Contract

- Format: json
- Required fields: objective_ref, scope_baseline_ref

## Fail-Closed 决策

1. 缺失 `objective_context_ref` 或引用不可达：返回 `2` 并拒绝推进。
2. 下游 `meta.arch.objective-writer` 未通过：返回 `2` 并落盘 fail 证据。
3. 运行异常：返回 `1`。

## 运行命令

```bash
# Happy path
python3 processes/meta/objective-scope-baseline/scripts/objective_scope_baseline_runner.py \
  --input tmp/session5/objective_scope_input.json \
  --output tmp/session5/objective_scope_output.json \
  --evidence-dir tmp/session5/objective_scope_evidence

# Fail-Closed path（缺 objective_context_ref）
python3 processes/meta/objective-scope-baseline/scripts/objective_scope_baseline_runner.py \
  --input tmp/session5/objective_scope_input_missing_ref.json \
  --output tmp/session5/objective_scope_output_missing_ref.json \
  --evidence-dir tmp/session5/objective_scope_evidence_missing_ref
```

## 返回码语义

1. `0`：执行成功，产出 `objective_ref` 与 `scope_baseline_ref`。
2. `2`：Fail-Closed（输入缺失、引用不可达、子流程失败）。
3. `1`：运行异常（非业务 Fail-Closed）。
