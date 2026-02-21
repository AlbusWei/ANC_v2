# AP-007 Objective Evaluation

> 版本: v0.4.0 | 层级: P6 | 类型: 原子流程

- Actor: qa / qa-engineer
- Skill: sys.qa.evaluation-runner（CLI: `quality_eval_runner`）
- Input:
  - preparation_bundle_ref
  - actual_output_refs
- Bundle dereference:
  - test_datapoints_ref
  - tc_profile_map_ref
  - compile_report_ref
- Execution:
  - 先执行规则/契约校验
  - 再执行 objective profile（内含 `meta.qa.llm-judge` 评估配置）
- Output:
  - objective_eval_ref
  - objective_eval_verdict（`pass|fail|hold|test_invalid`）
  - objective_eval_reasons[]
  - raw_eval_ref
- Fail-Closed:
  - 判定不可解析
  - 关键输入缺失
  - 证据缺失或不可追溯
- Evidence:
  - objective_eval_ref
  - raw_eval_ref
