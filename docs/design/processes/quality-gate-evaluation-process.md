# Quality Gate Evaluation Process

> 版本: v0.2.0 | 层级: P4 | 类型: 复合流程 | process_id: quality-gate-evaluation

## 目标

在实现产物就绪后执行客观/主观/回归评测，并产出统一 `gate_decision` 与可审计证据包。

## 连续性边界

1. 本流程只能在 `AP-006 implementation-execution` 之后启动。
2. 本流程不承担测试设计与编译职责。
3. 出现 `hold` 必须转入 `hold-governance`，不得在本流程内以硬超时直接失败。
4. AP-008 主观评测默认启用，除非上级治理流程显式批准关闭。

## 阶段定义

1. `run-objective-evaluation`（AP-007）
2. `run-subjective-evaluation`（AP-008，默认启用）
3. `run-regression-evaluation`（AP-009）
4. `aggregate-gate-decision`（AP-020）

## 阶段到原子流程映射

| 阶段 | 原子流程 | 输出 |
|---|---|---|
| run-objective-evaluation | AP-007 | objective_eval_ref |
| run-subjective-evaluation | AP-008 | subjective_eval_ref |
| run-regression-evaluation | AP-009 | regression_eval_ref |
| aggregate-gate-decision | AP-020 | gate_decision + final_gate_verdict_ref |

## 输入契约

1. `preparation_bundle_ref`
2. `actual_output_refs`
3. `profile_set`（可选覆盖）

## 输出契约

1. `gate_decision`（`pass|fail|hold|test_invalid`）
2. `evidence_ref`
3. `reasons[]`
4. `final_gate_verdict_ref`
5. `raw_eval_ref`（可选）

## HOLD 路由规则

1. 任一分项评测返回 `hold` 时，转入 `docs/design/processes/hold-governance-process.md`。
2. HOLD 治理结束后仅允许回填 `continue|retry|debug|fail` 决策。

## Fail-Closed 规则

1. `preparation_bundle_ref` 缺失或不可解析 -> `fail`
2. 关键输入缺失 -> `fail`
3. 判定不可解析 -> `fail`
4. 证据不可追溯 -> `fail`
5. 任一 P0 `fail` -> 总体 `fail`

## 依赖流程

1. `docs/design/processes/atomic/AP-007-objective-evaluation.md`
2. `docs/design/processes/atomic/AP-008-subjective-evaluation.md`
3. `docs/design/processes/atomic/AP-009-regression-execution.md`
4. `docs/design/processes/atomic/AP-020-gate-decision-aggregation.md`
5. `docs/design/processes/hold-governance-process.md`

## 证据

1. `objective_eval_ref`
2. `subjective_eval_ref`
3. `regression_eval_ref`
4. `final_gate_verdict_ref`
