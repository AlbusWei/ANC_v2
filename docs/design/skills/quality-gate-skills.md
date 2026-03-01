# Quality Gate Skills 设计包

> 版本: v0.4.1 | 分类: System Skills | 最后更新: 2026-02-26

## 目标

定义统一质量门禁链路的技能集合，覆盖 `TEST.md` 编译、评测执行、门禁聚合、HOLD 治理、registry 校验与证据归档。

关联规范：

1. `docs/design/modules/M1-test-system.md`
2. `docs/design/modules/M1-openjudge-adapter-spec.md`
3. `docs/design/processes/quality-gate-preparation-process.md`
4. `docs/design/processes/quality-gate-evaluation-process.md`
5. `docs/design/processes/hold-governance-process.md`

## 技能定义卡

### 1. sys.qa.test-compiler

- 定位：将 `TEST.md` 变为可执行 datapoints，并产出 `tc_id -> profile_id` 映射。
- 输入契约：`test_doc_ref`, `objective_ref`, `spec_ref`, `profile_set`
- 输出契约：`test_datapoints_ref`, `tc_profile_map_ref`, `compile_report_ref`, `gate_decision`
- Fail-Closed：
  - `TEST.md` 不可解析 -> `test_invalid`
  - 编译产物与 test case 数量不一致 -> `fail`
  - profile 绑定缺失 -> `fail`
- test_mount：`skills/system/qa/test-compiler/TEST.md`
- 状态：`active`（Phase 1 pilot）

### 2. sys.qa.evaluation-runner

- 定位：统一评测执行入口，供 `AP-007/AP-008/AP-009` 调度。
- CLI：`quality_eval_runner`
- 执行机制：OpenJudge `GradingRunner` + 动态 grader 组合（由测试计划 `grader_selection/grader_weights/min_score_per_grader/must_pass_graders` 驱动），支持 `SimpleRubricsGenerator` 自动 rubric grader
- 主观评测：A/B 盲测使用 listwise 比较（`LLMGrader` 或自动 rubric listwise grader），记录 seed/rounds/blind assignment/judge_result
- 输入契约：`preparation_bundle_ref`, `superpower_ref`, `actual_output_refs`, `evaluation_mode`
- 输出契约：`raw_eval_ref`, `runner_log_ref`, `execution_state_ref`, `evaluation_verdict`
- Fail-Closed：
  - 执行协议无效 -> `fail|test_invalid`
  - 运行前契约错误 -> `test_invalid`
  - judge 模型不支持、鉴权失败、无效请求 -> `test_invalid`
- test_mount：`skills/system/qa/evaluation-runner/TEST.md`
- 状态：`active`（Phase 1 pilot）

### 3. sys.qa.verdict-normalizer

- 定位：把分项评测结果归一并输出最终 `gate_decision`。
- 输入契约：`objective_eval_ref`, `subjective_eval_ref`, `regression_eval_ref`, `aggregation_rules_ref`
- 输出契约：`gate_decision`, `runtime_gate_state`, `reasons`, `evidence_ref`, `final_gate_verdict_ref`
- Fail-Closed：
  - 任一关键评测包缺失 -> `fail`
  - 结果不可解析 -> `fail`
  - 输出 `runtime_gate_state=hold` 但 `gate_decision!=fail` -> `fail`
- test_mount：`skills/system/qa/verdict-normalizer/TEST.md`
- 状态：`active`（Phase 1 pilot）

### 4. sys.qa.hold-triage

- 定位：处理 `hold` 场景的证据采集、分类与动作执行。
- 输入契约：`hold_case_ref`, `runtime_log_ref`, `execution_state_ref`, `triage_policy_ref`
- 输出契约：`progress_signals_ref`, `triage_action`, `triage_report_ref`, `action_execution_ref`
- triage_action：`continue|retry|debug|fail`
- 升级链：`qa -> bpm -> admin`
- Fail-Closed：
  - 信号缺失且无法补证 -> `fail`
  - triage 无明确决策 -> `fail`
- test_mount：`skills/system/qa/hold-triage/TEST.md`
- 状态：`active`（Phase 1 pilot）

### 5. sys.qa.regression-runner

- 定位：执行跨模块回归并产出回归门禁候选结论。
- 输入契约：`regression_scope`, `profile_set`, `preparation_bundle_ref`, `actual_output_refs`
- 输出契约：`regression_eval_ref`, `regression_report_ref`, `release_gate_candidate`
- Fail-Closed：
  - 任一模块 P0 `fail` -> 阻断发布
  - 回归证据不可追溯 -> `fail`
- test_mount：`skills/system/qa/regression-runner/TEST.md`
- 状态：`active`（Phase 1 pilot）

### 6. sys.qa.registry-validator

- 定位：执行 registry contract 校验并输出结构化 gate 报告。
- 输入契约：`registry_tool_ref`, `verify_scope`, `output_dir`
- 输出契约：`validation_report_ref`, `gate_decision`, `evidence_ref`, `reasons`
- Fail-Closed：
  - verify 返回非零 -> `fail`
  - 报告结构异常 -> `fail`
- test_mount：`skills/system/qa/registry-validator/TEST.md`
- 状态：`active`（Phase 1 pilot）

### 7. sys.qa.evidence-archiver

- 定位：把评测结果归档为标准证据包并维护 traceability 索引。
- 输入契约：`run_id`, `profile_id`, `gate_decision`, `runtime_gate_state`, `actor`, `output_dir`
- 输出契约：`evidence_ref`, `evidence_index_ref`, `archive_report_ref`
- Fail-Closed：
  - gate_decision 枚举非法 -> `fail`
  - runtime_gate_state 枚举非法 -> `fail`
  - 必要元数据缺失 -> `fail`
- test_mount：`skills/system/qa/evidence-archiver/TEST.md`
- 状态：`active`（Phase 1 pilot）

## 生命周期与落盘状态

1. 本轮完成 `sys.qa.*` 七个技能资产标准化与最小脚本化实现。
2. 同步完成目录迁移到 `skills/system/qa/*`，并完成 registry 路径闭合。
3. review/active 证据：
   - `runtime_data/execution/evidence/quality-gate/review-round-1.md`
   - `runtime_data/execution/evidence/quality-gate/active-pilot-round-1.md`
   - `runtime_data/execution/evidence/quality-gate/runtime-validation-round-2/outputs/runtime_summary.json`
   - `runtime_data/execution/evidence/quality-gate/runtime-validation-round-3/outputs/runtime_summary.json`
   - `runtime_data/execution/evidence/quality-gate/runtime-validation-round-4/outputs/runtime_summary.json`
   - `runtime_data/execution/evidence/quality-gate/runtime-validation-round-5/outputs/runtime_summary.json`
4. runtime-validation-round-2 关键结论：
   - objective/regression 链路通过 OpenJudge 真执行产出 `pass`
  - subjective A/B 在平局时产出 `runtime_gate_state=hold`（对外门禁保持 `fail`，进入 hold 治理）
   - LLM-Judge 缺密钥时 Fail-Closed：`test_invalid`
5. runtime-validation-round-5 关键结论：
   - 七个 `sys.qa.*` 技能新增边界用例已落盘并可编译执行
   - 14 个补测用例全通过，Fail-Closed 与 traceability 输出符合预期
