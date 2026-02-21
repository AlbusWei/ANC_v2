# AP-031 Trigger Escalation Handling

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: sys.bpm.escalation-handler
- Input:
  - incident_ref
  - escalation_policy_ref
  - escalation_hint
  - evidence_ref
- Output:
  - escalation_ref
  - escalation_trace
  - final_owner
- Escalation chain:
  - `actor -> owner -> bpm -> admin -> human`
- Fail-Closed:
  - 升级链不完整或越级 -> `fail`
  - incident 证据缺失 -> `fail`
- Evidence:
  - escalation_ref
  - escalation_trace
