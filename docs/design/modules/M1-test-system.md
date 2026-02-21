# M1 — 测试系统模块详细设计

> 版本: v0.3.0 | 建设优先级: P0

## 模块定位

提供可复用的端到端测试与门禁能力，统一承担 Objective/Subjective 双轨评估、回归执行和治理放行判定。

## 模块边界

1. `M1` 负责“测试与门禁判定”，不负责生命周期状态迁移执行。
2. `M1` 对外输出结构化 verdict 与 gate decision，供 `M2/M3/M4/M5` 直接复用。
3. 各模块不得重复实现独立测试评估体系，应通过 `M1` 统一能力接入。

## 组件

1. llm-judge
2. test-designer
3. regression-runner
4. TEST 模板体系
5. contract-gate（`registry_contract_tool.py verify` 门禁能力）

## 依赖关系（类型化）

1. 依赖 `M2`（`R/E`）：通过 BPM 编排执行测试并回写证据链。
2. 依赖 `M6`（`E`）：对齐施工面阶段目标、风险与验收纪律。

## 对外能力（复用接口）

1. `test_plan` 生成：把 Objective/Spec 转换为可执行测试集合。
2. `evaluation_verdict` 输出：输出结构化通过/失败结论和置信度。
3. `regression_gate` 判定：发布前回归门禁，失败即阻断。
4. `contract_gate` 判定：契约与 Capability Contract 一致性校验门禁。

## 关键复用关系

1. `M3` 复用 `M1` 作为开发闭环的测试与放行门禁。
2. `M4` 复用 `M1` 作为 lifecycle 审查的测试基线。
3. `M5` 复用 `M1` 作为改进效果可验证判据。

## Fail-Closed 规则

1. 测试证据缺失或不可达时，默认判定为 `gate_fail`。
2. verdict 结构化字段缺失时，不允许推进生命周期状态。
3. 回归结果不确定或冲突时，按失败处理并升级 `owner -> bpm -> admin`。

## 风险与缓解

1. 风险：不同模块私有测试口径导致判定不一致。
缓解：统一通过 `M1` 输出标准 verdict 与 gate decision。
2. 风险：契约校验与测试校验分离导致漏检。
缓解：将 `contract_gate` 纳入 `M1` 一体化门禁流程。

## 关键流程挂载

- AP-005 test-design
- AP-007 objective-evaluation
- AP-008 subjective-evaluation
- AP-009 regression-execution

## 验收

- [ ] 结构化 verdict 输出稳定
- [ ] 回归失败可阻断发布
- [ ] 测试结果可回写 lifecycle-review
- [ ] `M3/M4/M5` 均复用 `M1` 门禁且无重复实现
- [ ] 契约校验与测试门禁形成统一放行判定
