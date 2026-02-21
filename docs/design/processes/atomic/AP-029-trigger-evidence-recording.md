# AP-029 Trigger Evidence Recording

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: sys.bpm.evidence-recorder
- Input:
  - trigger_id
  - instance_id
  - decision
  - evidence_payload_ref
- Output:
  - trigger_receipt_ref
  - evidence_index_ref
  - traceability_link_ref
- Fail-Closed:
  - trigger 或 instance 标识缺失 -> `fail`
  - 证据索引不可写入 -> `fail`
- Evidence:
  - trigger_receipt_ref
  - evidence_index_ref
