# 上下文传递 Schema

> 版本: v0.2.0 | SSOT 上游: `docs/architecture/context_protocol.md`

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
    "instance_id": "string",
    "parent_instance_id": "string",
    "lineage_ref": "string",
    "stack_depth": "integer"
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
  "parent_instance_id": "string (optional)",
  "lineage_ref": "string (required)",
  "stack_depth": "integer (required)",
  "phase_id": "string (required)",
  "actor": "string (required)",
  "skill": "string (required)",
  "input": {
    "objective_ref": "string",
    "spec_ref": "string",
    "additional_context": {}
  },
  "constraints": {
    "max_retries": "integer",
    "timeout": "string"
  }
}
```

## BPM 任务完成 Schema (Task Completion)

```json
{
  "instance_id": "string (required)",
  "lineage_ref": "string (required)",
  "stack_depth": "integer (required)",
  "phase_id": "string (required)",
  "actor": "string (required)",
  "status": "string (completed|failed, required)",
  "output_ref": "string (required)",
  "evidence": {
    "timestamp": "string",
    "decision": "string",
    "reason": "string"
  }
}
```

## 大上下文处理

1. 先摘要再引用原文。
2. 摘要必须保留 `process_lineage`。
3. 缺 lineage 信息时禁止跨层流转。
