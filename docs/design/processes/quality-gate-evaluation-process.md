# Quality Gate Evaluation Process

> 版本: v0.3.0 | 层级: P4 | 类型: 复合流程 | process_id: quality-gate-evaluation

## 目标

在实现产物就绪后执行客观/主观/回归评测，并产出统一 `gate_decision`（对外）与 `runtime_gate_state`（运行时治理）及可审计证据包。

## 连续性边界

1. 本流程只能在 `AP-006 implementation-execution` 之后启动。
2. 本流程不承担测试设计与编译职责。
3. 出现 `runtime_gate_state=hold` 必须转入 `hold-governance`，不得在本流程内以硬超时直接失败。
4. AP-008 主观评测默认启用，除非上级治理流程显式批准关闭。

## 生命周期与调度状态

1. Registry 生命周期：`review`（W3-B）。
2. Runtime 入口：`processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py`。
3. 调度样例用例：
   - `TC-QA-PROC-001`（主链路 `pass`）。
   - `TC-QA-PROC-002`（`hold` 路由到 `hold-governance`）。

## 协作骨架 v1（QA 试点）

1. 试点模式：phase 级 isolated session（每个 phase 新建独立会话）。
2. 启用方式：
   - `--enable-phase-dispatch`：启用 phase 分发。
   - `--dispatch-openclaw`：启用真实 OpenClaw 分发（否则仅落盘分发证据）。
   - `--dispatch-reset-openclaw-session`：真实分发时默认开启，确保同 actor 每 phase 新会话。
   - `--dispatch-strict-session-match`：真实分发时默认开启，保证会话绑定可核对。
3. phase 分发最小语义：
   - `purpose`：本阶段目标；
   - `input_ref`：输入上下文引用；
   - `done_definition`：完成标准；
   - `handoff_note`：交接说明。
4. 试点目标：先验证多会话协作主链路可运行，再补强契约细节。

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
| aggregate-gate-decision | AP-020 | gate_decision + runtime_gate_state + final_gate_verdict_ref |

## 输入契约

1. `preparation_bundle_ref`
2. `actual_output_refs`
3. `profile_set`（可选覆盖）

## 输出契约

1. `gate_decision`（`pass|fail|test_invalid`）
2. `runtime_gate_state`（`pass|fail|hold|test_invalid`）
3. `evidence_ref`
4. `reasons[]`
5. `final_gate_verdict_ref`
6. `raw_eval_ref`（可选）

## HOLD 路由规则

1. 任一分项评测导致 `runtime_gate_state=hold` 时，转入 `docs/design/processes/hold-governance-process.md`。
2. 对外 `gate_decision` 在 hold 场景固定为 `fail`，HOLD 治理结束后仅允许回填 `continue|retry|debug|fail` 处置决策。
3. 仅在补测链路重新产出 `runtime_gate_state=pass` 时，对外 `gate_decision` 才允许恢复为 `pass`。

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

## W3-B 运行级证据

1. 套件报告：`runtime_data/execution/evidence/bpm-runtime/w3b_tc_qa_proc_report.json`
2. 主链路证据：`runtime_data/execution/evidence/bpm-runtime/w3b_qa_process_cases/TC-QA-PROC-001/`
3. HOLD 路由证据：`runtime_data/execution/evidence/bpm-runtime/w3b_qa_process_cases/TC-QA-PROC-002/`

<!-- phase-semantics-v2:start -->
## 阶段协作语义补充（v2）

> 说明：本节用于说明每个 phase 在系统主线中的职责与协作价值，要求可直接回答“为什么由该 Actor 在该阶段执行该动作”。

| phase_id | Actor | 阶段目的 | 输入语义 | 完成标准 | 交接语义 |
|---|---|---|---|---|---|
| `p1` | `qa` | 执行客观评测 profile。 | preparation_bundle_ref + actual_output_refs | 产出 objective_eval_ref，并满足：目标评测结论可解析且可追溯 | 将 objective_eval_ref 交接给 p2 |
| `p2` | `qa` | 默认执行盲评主观评测。 | preparation_bundle_ref + actual_output_refs + subjective_plan | 产出 subjective_eval_ref，并满足：主观评测记录包含 seed 轮次与结论 | 将 subjective_eval_ref 交接给 p3 |
| `p3` | `qa` | 执行跨模块回归评测。 | preparation_bundle_ref + profile_set + actual_output_refs | 产出 regression_eval_ref，并满足：回归报告包含模块级结论 | 将 regression_eval_ref 交接给 p4 |
| `p4` | `qa` | 汇总形成统一门禁结论。 | objective_eval_ref + subjective_eval_ref + regression_eval_ref | 产出 gate_decision + runtime_gate_state，并满足：门禁决策遵循统一 verdict 枚举与 P0 优先规则 | 将 gate_decision + runtime_gate_state 交接给 initiator |
| `p5` | `bpm` | 将 hold 案例路由至 hold 治理子流程。 | hold_case_ref + final_gate_verdict_ref | 产出 hold_resolution_ref，并满足：hold 案例在证据支撑下被解决或升级 | 将 hold_resolution_ref 交接给 initiator |
<!-- phase-semantics-v2:end -->
