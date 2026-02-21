# BPM ↔ Actor 通信协议

> 版本: v0.2.0 | SSOT 上游: `docs/architecture/process_architecture.md`

## 概述

定义 BPM 与 Actor（Agent）之间的任务分发和结果回收协议，支持递归流程栈帧隔离。

## 任务分发 (BPM → Actor)

### 请求格式

```json
{
  "type": "task_dispatch",
  "instance_id": "string (required)",
  "parent_instance_id": "string (optional)",
  "lineage_ref": "string (required)",
  "stack_depth": "integer (required)",
  "phase_id": "string (required)",
  "phase_name": "string (required)",
  "actor": "string (agent_id, required)",
  "skill": "string (skill_id, required)",
  "input": {
    "objective_ref": "string",
    "spec_ref": "string",
    "previous_output_ref": "string",
    "additional": {}
  },
  "constraints": {
    "max_retries": "integer",
    "timeout": "string (ISO8601 duration)"
  },
  "evidence_dir": "string (required)"
}
```

## 任务完成 (Actor → BPM)

```json
{
  "type": "task_completion",
  "instance_id": "string (required)",
  "lineage_ref": "string (required)",
  "stack_depth": "integer (required)",
  "phase_id": "string (required)",
  "actor": "string (required)",
  "status": "string (completed|failed, required)",
  "output_ref": "string (required)",
  "evidence": {
    "timestamp": "string (ISO8601, required)",
    "decision": "string (pass|fail, required)",
    "reason": "string (required)"
  }
}
```

## 错误处理

| 错误类型 | BPM 行为 |
|---|---|
| Actor 无响应 | 超时后标记失败，触发重试 |
| Skill 执行失败 | 记录失败证据，按 fail_policy 处理 |
| 输出格式错误 | 标记失败，要求重试 |
| 证据不完整 | Fail-Closed，阻止推进 |
| 递归深度超限 | 立即 fail 并升级 |

## 重试协议

1. BPM 检查 `fail_policy.max_retries`。
2. 重试未耗尽则重新分发并附失败原因。
3. 耗尽时执行 `escalate` 或 `cancel`。

## 通信方式

Phase 0-2 采用文件系统间接通信；Phase 3+ 可扩展消息队列/RPC。
