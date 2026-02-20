# AP-010 Lifecycle Transition

> 版本: v0.2.0 | 层级: P6 | 类型: 原子流程

- Actor: hr
- Skill: lifecycle-transition
- Input: asset_id, from_status, to_status, evidence_ref
- Output: transition record
- Fail-Closed: 非法状态迁移或缺证据直接拒绝
- Evidence: lifecycle_transition_ref
