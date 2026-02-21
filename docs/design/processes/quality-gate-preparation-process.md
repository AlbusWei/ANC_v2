# Quality Gate Preparation Process

> 版本: v0.1.0 | 层级: P4 | 类型: 复合流程 | process_id: quality-gate-preparation

## 目标

在实现执行前完成测试设计、datapoint 编译与 profile 绑定，产出可直接交付评测执行流程的标准化准备包。

## 连续性边界

1. 本流程位于开发断点之前。
2. 本流程结束后应进入 `AP-006 implementation-execution`。
3. 评测执行由独立流程 `quality-gate-evaluation` 在实现后触发。

## 阶段定义

1. `design-tests`（AP-005）
2. `compile-test-datapoints`（AP-018）
3. `bind-test-profiles`（AP-019）

## 阶段到原子流程映射

| 阶段 | 原子流程 | 输出 |
|---|---|---|
| design-tests | AP-005 | test_plan + test_cases |
| compile-test-datapoints | AP-018 | test_datapoints_ref + compile_report_ref |
| bind-test-profiles | AP-019 | tc_profile_map_ref + preparation_bundle_ref |

## 输入契约

1. `objective_ref`
2. `spec_ref`
3. `test_doc_ref`（唯一源 `TEST.md`）
4. `risk_focus`（必须覆盖 P0）

## 输出契约

1. `preparation_bundle_ref`（唯一主输出）
2. `preparation_evidence_ref`

`preparation_bundle` 索引字段最小集合：

1. `objective_ref`
2. `spec_ref`
3. `test_doc_ref`
4. `test_datapoints_ref`
5. `tc_profile_map_ref`
6. `compile_report_ref`
7. `producer_process_id`
8. `timestamps`

## Fail-Closed 规则

1. P0 场景缺失 -> `fail`
2. 编译期或运行前契约错误 -> `test_invalid`
3. `tc_id -> profile_id` 映射缺失 -> `fail`
4. 准备包证据不可追溯 -> `fail`

## 依赖流程

1. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/atomic/AP-005-test-design.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/atomic/AP-018-test-datapoint-compilation.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/atomic/AP-019-test-profile-binding.md`

## 证据

1. `test_plan_ref`
2. `compile_report_ref`
3. `tc_profile_map_ref`
4. `preparation_bundle_ref`
