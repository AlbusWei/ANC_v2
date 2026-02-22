# test-compiler Output Schema

输出 JSON 最小字段：

1. `test_datapoints_ref`
2. `tc_profile_map_ref`
3. `compile_report_ref`
4. `gate_decision`
5. `evidence_ref`
6. `reasons[]`

`test_datapoints_ref` 内容要求（最小）：

1. `datapoints[].tc_id`
2. `datapoints[].priority`
3. `datapoints[].evaluation_method`
4. `datapoints[].expected_conditions`
5. `datapoints[].judge_payload`（可为空）
6. `datapoints[].grader_selection/grader_weights/min_score_per_grader/must_pass_graders`（可选，动态计划字段）
7. `metadata.evaluation_configuration`（含 `subjective_seed` 与默认 grader 计划字段）

判定规则：

- parse 失败 -> `test_invalid`
- 缺失 P0 -> `fail`
- 其余 -> `pass`
