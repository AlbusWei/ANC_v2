# Role Responsibility Schemas

> 版本: v0.2.0

## Role Definition Schema

```json
{
  "role_id": "string",
  "agent_id": "string",
  "domain": "analysis|product|architecture|development|qa|release|delivery|ops",
  "responsibilities": ["string"],
  "decision_scope": ["string"],
  "non_scope": ["string"],
  "handoff_in": ["role_id"],
  "handoff_out": ["role_id"]
}
```

## Handoff Record Schema

```json
{
  "handoff_id": "string",
  "instance_id": "string",
  "from_role": "string",
  "to_role": "string",
  "input_ref": "string",
  "output_contract": {"required": ["string"]},
  "acceptance_criteria": ["string"],
  "status": "created|accepted|rejected|completed",
  "evidence_ref": "string"
}
```

## 规则

1. 每个交接记录必须可映射到 BPM 实例。
2. `from_role` 与 `to_role` 必须是已定义角色。
3. `completed` 状态必须带证据引用。
