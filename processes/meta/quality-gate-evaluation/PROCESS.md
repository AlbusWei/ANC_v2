# quality-gate-evaluation - Process Guide

## Purpose

对实现产物执行统一评测并产出可审计门禁结论。

## Entry Conditions

1. `preparation_bundle_ref` 可解析。
2. 实现产物已完成并可引用。
3. profile 设置可解析（默认含 subjective 评测）。

## Execution Phases

1. `p1 run-objective-evaluation`（qa / `sys.qa.evaluation-runner`）
2. `p2 run-subjective-evaluation`（qa / `sys.qa.evaluation-runner`）
3. `p3 run-regression-evaluation`（qa / `sys.qa.regression-runner`）
4. `p4 aggregate-gate-decision`（qa / `sys.qa.verdict-normalizer`）
5. `p5 govern-hold`（bpm / `hold-governance`，仅 hold 路由）

## Rejection Rules (Fail-Closed)

1. `preparation_bundle_ref` 缺失或不可解析。
2. 关键评测包不可解析。
3. 证据不可追溯。

## Primary Evidence Bundle

- `objective_eval_ref`
- `subjective_eval_ref`
- `regression_eval_ref`
- `final_gate_verdict_ref`
