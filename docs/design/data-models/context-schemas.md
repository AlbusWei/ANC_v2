# 上下文传递 Schema

> 版本: v0.5.0 | SSOT 上游: `docs/architecture/context_protocol.md`

## 概述

跨 Agent 上下文通过文档传递。递归流程上下文必须包含 lineage 信息。

## 阶段交接 Schema (Phase Handoff)

```json
{
  "objective_ref": "string (required)",
  "phase_id": "string (required)",
  "input_ref": "string (required)",
  "output_ref": "string (required)",
  "process_lineage": {
    "instance_id": "string (required)",
    "parent_instance_id": "string (required when recursive)",
    "lineage_ref": "string (required)",
    "stack_depth": "integer (required)",
    "session_binding": {
      "agent_id": "string (required)",
      "session_key": "string (required)",
      "session_id": "string (required)",
      "parent_session_id": "string|null (required)"
    }
  },
  "upstream_decision_refs": ["string"],
  "acceptance_criteria": ["string"],
  "known_risks": ["string"],
  "next_actions": ["string"]
}
```

## BPM 任务分发 Schema (Task Dispatch)

```json
{
  "instance_id": "string (required)",
  "phase_id": "string (required)",
  "actor": "string (required)",
  "target_type": "string (subprocess, required)",
  "target_id": "string (process_id 或 inline_ap.ap_id, required)",
  "input_ref": "string (required)",
  "objective_ref": "string (required)",
  "output_contract": "string (contract_ref, required)",
  "lineage_ref": "string (required)",
  "stack_depth": "integer (required)",
  "process_version": "string (required)",
  "process_level": "string (P1|P2|P3|P4|P5|P6, required)",
  "session_binding": {
    "agent_id": "string (required)",
    "session_key": "string (required)",
    "session_id": "string (required)",
    "parent_session_id": "string|null (required)"
  },
  "evidence_dir": "string (required)",
  "parent_instance_id": "string (optional)",
  "spec_ref": "string (required when phase.requires_spec=true)",
  "constraints": {
    "max_retries": "integer",
    "timeout": "string"
  }
}
```

Dispatch 约束：

1. `target_type` 固定为 `subprocess`。
2. `target_id` 命中 `process_registry` 时视为常规子流程。
3. `target_id` 未命中 `process_registry` 时，phase 必须声明 `inline_ap`，且 `inline_ap.skill_id` 命中 `skill_registry`。
4. `inline_ap.pierce_allowed=true` 时，要求 `inline_ap.actor == phase.actor`。

## BPM 任务完成 Schema (Task Completion)

```json
{
  "instance_id": "string (required)",
  "phase_id": "string (required)",
  "actor": "string (required)",
  "lineage_ref": "string (required)",
  "stack_depth": "integer (required)",
  "session_id": "string (required)",
  "status": "string (completed|failed, required)",
  "output_ref": "string (required)",
  "evidence_ref": "string (required)",
  "self_check": {
    "decision": "string (required)",
    "reason": "string (required)",
    "rule_refs": [
      "docs/architecture/process_architecture.md#bpm-protocol-canonical-schema-machine-readable"
    ]
  }
}
```

## 大上下文处理

1. 先摘要再引用原文。
2. 摘要必须保留 `process_lineage`。
3. 缺 lineage 信息时禁止跨层流转。
4. 缺 `session_binding.session_id` 或 actor 回执 `session_id` 时必须 Fail-Closed。
