# BPM ↔ Actor 通信协议

> 版本: v0.3.0 | SSOT 上游: `docs/architecture/process_architecture.md`

## 概述

定义 BPM 与 Actor（Agent）之间的任务分发和结果回收协议，支持递归流程栈帧隔离。

## 任务分发 (BPM → Actor)

### 请求格式

```json
{
  "type": "task_dispatch",
  "instance_id": "string (required)",
  "phase_id": "string (required)",
  "actor": "string (agent_id, required)",
  "target_type": "string (skill|subprocess, required)",
  "target_id": "string (registry stable id, required)",
  "input_ref": "string (required)",
  "objective_ref": "string (required)",
  "output_contract": "string (contract_ref, required)",
  "lineage_ref": "string (required)",
  "stack_depth": "integer (required)",
  "evidence_dir": "string (required)",
  "parent_instance_id": "string (optional)",
  "spec_ref": "string (required when phase.requires_spec=true)",
  "constraints": {
    "max_retries": "integer",
    "timeout": "string (ISO8601 duration)"
  }
}
```

约束：

1. `target_type=skill` 时，`target_id` 必须命中 `shared/registry/skill_registry.json#entries[].skill_id`。
2. `target_type=subprocess` 时，`target_id` 必须命中 `shared/registry/process_registry.json#entries[].process_id`。
3. 禁止使用旧字段：`skill`、`skill_or_process`、`skill_or_subprocess`。

## 任务完成 (Actor → BPM)

```json
{
  "type": "task_completion",
  "instance_id": "string (required)",
  "phase_id": "string (required)",
  "actor": "string (required)",
  "lineage_ref": "string (required)",
  "stack_depth": "integer (required)",
  "status": "string (completed|failed, required)",
  "output_ref": "string (required)",
  "evidence_ref": "string (required)",
  "self_check": {
    "decision": "string (pass|fail, required)",
    "reason": "string (required)",
    "rule_refs": [
      "docs/architecture/process_architecture.md#bpm-protocol-canonical-schema-machine-readable"
    ]
  }
}
```

## 错误处理

| 错误类型 | BPM 行为 |
|---|---|
| Actor 无响应 | 超时后标记失败，触发重试 |
| Target 不可解析 | Fail-Closed，阻止推进 |
| 输出格式错误 | 标记失败，要求重试 |
| 证据不完整 | Fail-Closed，阻止推进 |
| 递归深度超限 | 立即失败并升级 |

## 重试协议

1. BPM 检查 `constraints.max_retries`。
2. 重试未耗尽则重新分发并附失败原因。
3. 耗尽时执行 `escalate` 或 `cancel`。

## 通信方式

Phase 0-2 采用文件系统间接通信；Phase 3+ 可扩展消息队列/RPC。
