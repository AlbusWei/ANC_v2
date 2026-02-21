# Quality Gate Skills 设计包

> 版本: v0.3.0 | 分类: System Skills | 最后更新: 2026-02-21

## 目标

定义统一质量门禁链路的技能集合，覆盖 `TEST.md` 编译、评测执行、门禁聚合与 HOLD 治理。

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
- 输出契约：`test_datapoints_ref`, `tc_profile_map_ref`, `compile_report_ref`
- Fail-Closed：
  - `TEST.md` 不可解析 -> `test_invalid`
  - 编译产物与 test case 数量不一致 -> `fail`
  - profile 绑定缺失 -> `fail`
- test_mount：`skills/system/test-compiler/TEST.md`
- 状态：`draft`（已注册）

### 2. sys.qa.evaluation-runner

- 定位：统一评测执行入口，供 `AP-007/AP-008/AP-009` 调度。
- CLI：`quality_eval_runner`
- 输入契约：`preparation_bundle_ref`, `actual_output_refs`, `evaluation_mode`
- 输出契约：`raw_eval_ref`, `runner_log_ref`, `execution_state_ref`, `evaluation_verdict`
- Fail-Closed：
  - 执行协议无效 -> `fail`
  - 运行前契约错误 -> `test_invalid`
- test_mount：`skills/system/evaluation-runner/TEST.md`
- 状态：`draft`（已注册）

### 3. sys.qa.verdict-normalizer

- 定位：把分项评测结果归一并输出最终 `gate_decision`。
- 输入契约：`objective_eval_ref`, `subjective_eval_ref`, `regression_eval_ref`, `aggregation_rules_ref`
- 输出契约：`gate_decision`, `reasons`, `evidence_ref`, `final_gate_verdict_ref`
- Fail-Closed：
  - 任一关键评测包缺失 -> `fail`
  - 结果不可解析 -> `fail`
- test_mount：`skills/system/verdict-normalizer/TEST.md`
- 状态：`draft`（已注册）

### 4. sys.qa.hold-triage

- 定位：处理 `hold` 场景的证据采集、分类与动作执行。
- 输入契约：`hold_case_ref`, `runtime_log_ref`, `execution_state_ref`, `triage_policy_ref`
- 输出契约：`progress_signals_ref`, `triage_action`, `triage_report_ref`, `action_execution_ref`
- triage_action：`continue|retry|debug|fail`
- 升级链：`qa -> bpm -> admin`
- Fail-Closed：
  - 信号缺失且无法补证 -> `fail`
  - triage 无明确决策 -> `fail`
- test_mount：`skills/system/hold-triage/TEST.md`
- 状态：`draft`（已注册）

### 5. sys.qa.regression-runner

- 定位：执行跨模块回归并产出回归门禁候选结论。
- 输入契约：`regression_scope`, `profile_set`, `preparation_bundle_ref`, `actual_output_refs`
- 输出契约：`regression_eval_ref`, `regression_report_ref`, `release_gate_candidate`
- Fail-Closed：
  - 任一模块 P0 `fail` -> 阻断发布
  - 回归证据不可追溯 -> `fail`
- test_mount：`skills/system/regression-runner/TEST.md`
- 状态：`draft`（已注册）

## 生命周期与落盘状态

1. `sys.qa.*` 五个技能均已落盘并进入 registry `draft`。
2. 进入 `review` 前置：
   - 对应运行级证据（至少一轮流程执行证据）
   - `registry_contract_tool.py verify` 持续通过
3. 进入 `active` 前置：
   - 与 AP-005/007/008/009/018/019/020/021/022/023 契约验证通过
   - M3/M4/M5 复用接入证据齐备
