# 流程实例 Schema

> 版本: v0.2.0 | SSOT 上游: `docs/architecture/process_architecture.md`

## 流程定义 Schema (process.json)

```json
{
  "process_id": "string (kebab-case, required)",
  "version": "string (semver, required)",
  "process_level": "string (P1|P2|P3|P4|P5|P6, required)",
  "parent_process_id": "string (optional)",
  "composed_processes": ["string (process_id)"] ,
  "lineage_policy": {
    "stack_isolation": "boolean",
    "allow_same_level_composition": "boolean",
    "max_stack_depth": "integer"
  },
  "objective_ref": "string (Objective 路径)",
  "phases": [{
    "phase_id": "string (p1, p2, ..., required)",
    "name": "string (kebab-case, required)",
    "actor": "string (agent_id, required)",
    "skill": "string (skill_id, required)",
    "sipoc": {
      "supplier": "string (required)",
      "input": "string (required)",
      "process": "string (required)",
      "output": "string (required)",
      "client": "string (required)"
    }
  }],
  "control_flow": [{
    "type": "string (sequence|condition|loop|fork_join|merge)",
    "from": "string (phase_id)",
    "to": "string (phase_id)",
    "condition": "string (optional)",
    "max_iterations": "integer (loop 类型必填)"
  }],
  "fail_policy": {
    "max_retries": "integer (默认 1)",
    "on_exhaust": "string (escalate|cancel)"
  }
}
```

## 流程实例 Schema (context.json)

```json
{
  "instance_id": "string (run-{process}-{date}-{seq}, required)",
  "parent_instance_id": "string (optional)",
  "lineage_ref": "string (required)",
  "stack_depth": "integer (required)",
  "process_id": "string (required)",
  "process_version": "string (required)",
  "process_level": "string (P1~P6, required)",
  "objective_ref": "string (required)",
  "initiated_by": "string (agent_id, required)",
  "status": "string (created|running|waiting|completed|failed|cancelled|archived)",
  "created_at": "string (ISO8601)",
  "updated_at": "string (ISO8601)",
  "current_phase": "string (phase_id)",
  "phase_results": [{
    "phase_id": "string",
    "status": "string (completed|failed|skipped)",
    "actor": "string",
    "input_ref": "string",
    "output_ref": "string",
    "started_at": "string (ISO8601)",
    "completed_at": "string (ISO8601)"
  }]
}
```

## 实例状态机

```
Created → Running → Waiting → Completed
                  ↘         ↗
                   Failed
                  ↘
                   Cancelled

Completed|Failed|Cancelled → Archived
```

## 递归执行约束

1. 子流程必须创建独立实例。
2. 子流程不得直接写父流程运行状态。
3. 父流程只消费子流程契约输出。
4. stack_depth 超过阈值必须 Fail-Closed。
