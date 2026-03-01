# BPM ↔ Actor 通信协议

> 版本: v0.5.0 | SSOT 上游: `docs/architecture/process_architecture.md`

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
    "timeout": "string (ISO8601 duration)"
  }
}
```

约束：

1. `target_type` 仅允许 `subprocess`。
2. `target_id` 命中 `process_registry.process_id` 时，按常规子流程处理。
3. `target_id` 未命中 `process_registry` 时，必须在 phase 中声明 `inline_ap`，且 `inline_ap.skill_id` 命中 `skill_registry.skill_id`。
4. `inline_ap.pierce_allowed=true` 时，要求 `inline_ap.actor == phase.actor`，并允许同 Actor 穿透执行。
5. 禁止使用旧字段：`skill`、`skill_or_process`、`skill_or_subprocess`。
6. BPM 调 OpenClaw 时必须显式传 `--session-id <session_binding.session_id>`，禁止隐式主会话执行。
7. 子实例 `session_binding.session_id` 必须与 `parent_session_id` 不同。

## 任务完成 (Actor → BPM)

```json
{
  "type": "task_completion",
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
