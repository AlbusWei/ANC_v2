# AP-009 Regression Execution

> 版本: v0.4.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.regression-runner
- Input:
  - preparation_bundle_ref
  - regression_scope
  - target_assets（M3/M4/M5）
  - profile_set（baseline + module delta）
  - actual_output_refs
- Bundle dereference:
  - test_datapoints_ref
  - tc_profile_map_ref
- Execution note:
  - regression-runner 内部以 regression mode 调度 `sys.qa.evaluation-runner`
- Output:
  - regression_eval_ref
  - regression_report_ref
  - release_gate_candidate
- Gate Rules:
  - 任一模块 P0 用例 `fail` -> 阻断发布
  - 存在 `hold` 且无 `fail` -> 转入 HOLD governance
- HOLD Governance:
  - 路由流程：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/hold-governance-process.md`
  - triage 决策：`continue|retry|debug|fail`
- Fail-Closed:
  - 回归证据缺失
  - 结果不可解析
  - 关键输入缺失
- Evidence:
  - regression_eval_ref
  - regression_report_ref
