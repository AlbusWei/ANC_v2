# Quality Gate Preparation Process

> 版本: v0.1.1 | 层级: P4 | 类型: 复合流程 | process_id: quality-gate-preparation

## 目标

在实现执行前完成测试设计、datapoint 编译与 profile 绑定，产出可直接交付评测执行流程的标准化准备包。

## 连续性边界

1. 本流程位于开发断点之前。
2. 本流程结束后应进入 `AP-006 implementation-execution`。
3. 评测执行由独立流程 `quality-gate-evaluation` 在实现后触发。

## 生命周期与调度状态

1. Registry 生命周期：`review`（W3-B）。
2. Runtime 入口：`processes/meta/quality-gate-preparation/scripts/quality_gate_preparation_runner.py`。
3. 调度样例用例：`TC-QA-PROC-001`（主链路前半段）。

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
5. `superpower_ref`（必须可达，用于对齐 Superpower 主链执行上下文）

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
5. `superpower_ref` 缺失或不可达 -> `fail`

## 依赖流程

1. `docs/design/processes/atomic/AP-005-test-design.md`
2. `docs/design/processes/atomic/AP-018-test-datapoint-compilation.md`
3. `docs/design/processes/atomic/AP-019-test-profile-binding.md`

## 证据

1. `test_plan_ref`
2. `compile_report_ref`
3. `tc_profile_map_ref`
4. `preparation_bundle_ref`

## W3-B 运行级证据

1. 套件报告：`runtime_data/execution/evidence/bpm-runtime/w3b_tc_qa_proc_report.json`
2. Case 目录：`runtime_data/execution/evidence/bpm-runtime/w3b_qa_process_cases/TC-QA-PROC-001/`

<!-- phase-semantics-v2:start -->
## 阶段协作语义补充（v2）

> 说明：本节用于说明每个 phase 在系统主线中的职责与协作价值，要求可直接回答“为什么由该 Actor 在该阶段执行该动作”。

| phase_id | Actor | 阶段目的 | 输入语义 | 完成标准 | 交接语义 |
|---|---|---|---|---|---|
| `p1` | `qa` | 设计与目标对齐且覆盖 P0 风险的测试。 | objective_ref + spec_ref + test_doc_ref + superpower_ref | 产出 test_plan_ref，并满足：P0 风险覆盖显式且可追溯 | 将 test_plan_ref 交接给 p2 |
| `p2` | `qa` | 将 TEST.md 编译为可执行数据点。 | test_plan_ref + test_doc_ref | 产出 test_datapoints_ref + compile_report_ref，并满足：编译报告完整且数据点可执行 | 将 test_datapoints_ref + compile_report_ref 交接给 p3 |
| `p3` | `qa` | 绑定 tc_id 与 profile_id 并打包准备集。 | test_datapoints_ref + compile_report_ref + profile_set + superpower_ref | 产出 preparation_bundle_ref，并满足：tc_id 与 profile_id 映射一一对应且可追溯 | 将 preparation_bundle_ref 交接给 initiator |
<!-- phase-semantics-v2:end -->
