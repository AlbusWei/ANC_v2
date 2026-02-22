# AP-034 Linked Artifacts Update

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: architect
- Skill: system.ops.manual-task
- Input:
  - round_id
  - linkage_report_ref
  - changed_assets
- Output:
  - m6_update_bundle_ref
  - construction_plane_delta_ref
  - open_questions_ref
- Fail-Closed:
  - linkage_report_ref 不可达
  - 联动缺口未补齐仍尝试推进
  - 开放问题缺 owner 或下一步
- Evidence:
  - m6_update_bundle_ref
  - construction_plane_delta_ref
