# AP-019 Test Profile Binding

> 版本: v0.1.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.test-compiler（profile-binding mode）
- Input:
  - test_datapoints_ref
  - profile_set
  - compile_report_ref
- Output:
  - tc_profile_map_ref
  - preparation_bundle_ref
- Fail-Closed:
  - tc_id 与 profile_id 无法一一映射 -> `fail`
  - profile 越权覆盖不可变门禁字段 -> `fail`
  - preparation bundle 索引缺字段 -> `fail`
- Evidence:
  - tc_profile_map_ref
  - preparation_bundle_ref
