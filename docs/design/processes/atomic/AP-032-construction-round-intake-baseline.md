# AP-032 Construction Round Intake Baseline

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: bpm
- Skill: system.ops.manual-task
- Input:
  - round_id
  - round_goal
  - change_scope_ref
  - changed_assets
  - linkage_targets
  - owner
  - openspec_ref（架构相关变更必填）
- Output:
  - scope_baseline_ref
- Fail-Closed:
  - round_id 格式不合法或缺失
  - change_scope_ref 不可达
  - changed_assets/linkage_targets 为空
- Evidence:
  - scope_baseline_ref
