# quality-gate-preparation - Process Guide

## Purpose

将测试准备阶段标准化为可编排流程，确保后续评测有稳定输入。

## Entry Conditions

1. Objective 与 Spec 已冻结并可引用。
2. `TEST.md` 已提交为唯一测试定义源。
3. 风险范围包含 P0 场景。

## Execution Phases

1. `p1 design-tests`（qa / `meta.qa.test-designer`）
2. `p2 compile-test-datapoints`（qa / `sys.qa.test-compiler`）
3. `p3 bind-test-profiles`（qa / `sys.qa.test-compiler`）

## Rejection Rules (Fail-Closed)

1. P0 场景缺失。
2. TEST 编译失败且不可修复。
3. profile 绑定缺失或越权。

## Primary Evidence Bundle

- `test_plan_ref`
- `compile_report_ref`
- `tc_profile_map_ref`
- `preparation_bundle_ref`
