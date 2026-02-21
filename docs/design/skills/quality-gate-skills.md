# Quality Gate Skills 设计包

> 版本: v0.2.0 | 分类: System Skills | 最后更新: 2026-02-21

## 目标

定义统一质量门禁链路的技能集合，覆盖 `TEST.md` 编译、评测执行、门禁聚合与 HOLD 治理。

关联规范：

1. `/Users/albus/MyProjects/ANC_v2/docs/design/modules/M1-test-system.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/design/modules/M1-openjudge-adapter-spec.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/quality-gate-preparation-process.md`
4. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/quality-gate-evaluation-process.md`
5. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/hold-governance-process.md`

## 技能定义卡

### 1. sys.qa.test-compiler

- 定位：将 `TEST.md` 变为可执行 datapoints，并在 profile-binding mode 产出 `tc_id -> profile_id` 映射。
- 输入契约：`test_doc_ref`, `objective_ref`, `spec_ref`, `profile_set`（可选）
- 输出契约：`test_datapoints_ref`, `tc_profile_map_ref`, `compile_report_ref`
- Fail-Closed：
  - `TEST.md` 不可解析 -> `test_invalid`
  - 编译产物与 test case 数量不一致 -> `fail`
  - profile 绑定缺失 -> `fail`
- test_mount 计划：
  - `test_doc`: `/Users/albus/MyProjects/ANC_v2/tests/system/quality-gate/test-compiler/TEST.md`
  - `methodology_ref`: `/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md`

### 2. sys.qa.evaluation-runner

- 定位：统一评测执行入口，供 `M2` 或 `AP-007/AP-008/AP-009` 调度。
- CLI：`quality_eval_runner`
- 输入契约：`preparation_bundle_ref`, `actual_output_refs`, `evaluation_mode`（`objective|subjective|regression`）
- 输出契约：`raw_eval_ref`, `runner_log_ref`, `execution_state_ref`
- 返回码：`0|20|30|40|50`（语义与旧 runner 保持一致）
- Fail-Closed：
  - 执行协议无效 -> `fail`
  - 运行前契约错误 -> `test_invalid`
- test_mount 计划：
  - `test_doc`: `/Users/albus/MyProjects/ANC_v2/tests/system/quality-gate/evaluation-runner/TEST.md`
  - `methodology_ref`: `/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md`

### 3. sys.qa.verdict-normalizer

- 定位：把分项评测结果归一并输出最终 `gate_decision`。
- 输入契约：`objective_eval_ref`, `subjective_eval_ref`（可选）, `regression_eval_ref`, `aggregation_rules_ref`
- 输出契约：`gate_decision`, `reasons`, `evidence_ref`, `final_gate_verdict_ref`
- Fail-Closed：
  - 任一关键评测包缺失 -> `fail`
  - 结果不可解析 -> `fail`
- test_mount 计划：
  - `test_doc`: `/Users/albus/MyProjects/ANC_v2/tests/system/quality-gate/verdict-normalizer/TEST.md`
  - `methodology_ref`: `/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md`

### 4. sys.qa.hold-triage

- 定位：处理 `hold` 场景的证据采集、分类与动作执行。
- 输入契约：`hold_case_ref`, `progress_signals_ref`, `triage_policy_ref`
- 输出契约：`triage_action`（`continue|retry|debug|fail`）, `triage_report_ref`
- 最小进展信号：日志增量、阶段推进、输出流心跳
- 升级链：`qa -> bpm -> admin`
- Fail-Closed：
  - 信号缺失且无法补证 -> `fail`
  - triage 无明确决策 -> `fail`
- test_mount 计划：
  - `test_doc`: `/Users/albus/MyProjects/ANC_v2/tests/system/quality-gate/hold-triage/TEST.md`
  - `methodology_ref`: `/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md`

### 5. sys.qa.regression-runner

- 定位：执行跨模块回归并产出回归门禁候选结论。
- 输入契约：`regression_scope`, `profile_set`, `preparation_bundle_ref`
- 输出契约：`regression_report_ref`, `regression_eval_ref`, `release_gate_candidate`
- Fail-Closed：
  - 任一模块 P0 `fail` -> 阻断发布
  - 回归证据不可追溯 -> `fail`
- test_mount 计划：
  - `test_doc`: `/Users/albus/MyProjects/ANC_v2/tests/system/quality-gate/regression-runner/TEST.md`
  - `methodology_ref`: `/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md`

## 生命周期与落盘状态

1. 当前状态：设计已落盘，技能资产待创建并进入 registry `draft`。
2. 激活前置：
   - 对应 `SKILL.md/TEST.md` 资产创建完成
   - `registry_contract_tool.py verify` 通过
   - 与 AP-005/018/019/020/021/022/023/024/025 及 AP-007/008/009 I/O 契约一致
