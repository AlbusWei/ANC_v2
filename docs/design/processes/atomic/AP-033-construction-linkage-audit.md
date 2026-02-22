# AP-033 Construction Linkage Audit

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: architect
- Skill: sys.arch.construction-audit
- Input:
  - round_id
  - scope_baseline_ref
  - linkage_targets
  - changed_assets
  - openspec_ref
- Output:
  - linkage_report_ref
  - missing_items
  - blocking_risks
  - recommended_actions
- Fail-Closed:
  - linkage_targets 缺失 design/inventory/registry/construction_plane 任一域
  - scope_baseline_ref 不可达或不包含回合边界信息
  - 证据引用不可达
  - 架构回合缺失 openspec_ref 或语义冲突无裁决
- Evidence:
  - linkage_report_ref
