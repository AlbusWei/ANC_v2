# M1 — 测试系统模块详细设计

> 版本: v0.5.2 | 建设优先级: P0 | 最后更新: 2026-02-26

## 模块定位

`M1` 是 ANC 的统一测试与门禁模块，负责把 Objective/Spec/Test 转换为可执行评测，并输出可审计 gate 判定。  
OpenJudge 在 `M1` 中定位为评测执行内核，不直接承担治理决策。

相关文档：

1. 适配接口：`docs/design/modules/M1-openjudge-adapter-spec.md`
2. 技能设计：`docs/design/skills/quality-gate-skills.md`
3. 准备流程：`docs/design/processes/quality-gate-preparation-process.md`
4. 评测流程：`docs/design/processes/quality-gate-evaluation-process.md`
5. HOLD 治理流程：`docs/design/processes/hold-governance-process.md`
6. Thread-3 运行级闭环证据：`tmp/runtime_data/execution/evidence/quality-gate/runtime-validation-round-6-m1-closure/runtime_summary.json`
7. 真实服务语义评审证据：`tmp/runtime_data/execution/evidence/quality-gate/runtime-validation-round-8-semantic-service/runtime_summary.json`

## Phase 1 成功优先级

1. 门禁真实生效：`gate_decision` 能阻断推进。
2. 全系统复用：`M3/M4/M5` 接入统一门禁协议。
3. verdict 稳定可解释：必须可解析为统一输出。
4. 成本与时延优化：不作为 Phase 1 首要成败判据。

## 模块边界

1. OpenJudge 仅产出 `raw eval`，不直接给最终 gate。
2. `M1 adapter` 负责 `raw eval -> unified verdict -> gate_decision`。
3. `M2` 全权管理运行状态机（running/hold/retry/debug/fail/complete）。
4. `M4` 独占生命周期状态推进（review/active/deprecated/retired）。
5. 各模块不得重复实现独立评测引擎，应通过 `M1` profile 复用。

## 组件

1. test-designer（测试计划与用例设计）
2. test-compiler（`TEST.md -> OpenJudge datapoints`）
3. evaluation-runner（统一 CLI 入口 `quality_eval_runner`）
4. llm-judge（语义评估能力）
5. regression-runner（回归执行与聚合候选）
6. verdict-normalizer（统一输出契约）
7. hold-triage（长时任务治理）
8. registry-validator（`registry_contract_tool.py verify` 封装门禁能力）
9. evidence-archiver（证据包索引归档与追溯输出）

实现约束补充（2026-02-21 runtime validation）：

1. `evaluation-runner` 必须通过 OpenJudge 真实执行 grader，禁止 marker-only 假评测。
2. `LLM-as-Judge` 需显式模型配置与凭据；凭据缺失必须 `test_invalid`（Fail-Closed）。
3. 评测证据需保留 raw grader 输出与可追溯索引。
4. grader 选择与权重应由测试计划动态驱动（`grader_selection/grader_weights/min_score_per_grader`），必要时使用 OpenJudge rubric 生成机制创建定制 grader。
5. 主观评测应采用 A/B 盲测 listwise 比较并记录 `seed/rounds/blind_assignment`，禁止把主观评测退化为固定模板单轮检查。
6. judge 模型/凭据/请求配置不可用时应 `test_invalid`（例如 provider 返回 unsupported model）。

## 流程连续性模型

1. 开发前：`quality-gate-preparation`（AP-005/018/019）。
2. 开发断点：`AP-006 implementation-execution`。
3. 开发后：`quality-gate-evaluation`（AP-007/008/009/020）。
4. 异常治理：出现 `hold` 时转入 `hold-governance`（AP-021~025）。

## 输入契约（统一源）

1. `TEST.md` 是唯一测试定义源：
   - 模板基线：`tests/template/TEST.md`
2. 交接输入采用 `preparation_bundle_ref`。
3. 评测流程的运行输入为 `preparation_bundle_ref + superpower_ref + actual_output_refs`。
4. `tc_id -> profile_id` 必须显式映射并纳入证据包。

## 输出契约（Unified Verdict）

必填字段：

```json
{
  "gate_decision": "pass|fail|test_invalid",
  "runtime_gate_state": "pass|fail|hold|test_invalid",
  "evidence_ref": "path/to/evidence_package",
  "reasons": ["..."]
}
```

可选字段白名单：

```json
{
  "raw_eval_ref": "path/to/raw_eval",
  "retry_hint": "retry|debug|manual-check",
  "profile_id": "quality-gate.baseline@1.0.0",
  "parser_notes": "..."
}
```

## 门禁与聚合规则

1. AP-007/AP-008/AP-009 产出分项评测结果。
2. AP-020 负责总聚合并输出最终 `gate_decision`。
3. P0 聚合：
   - 任一 P0 `fail` -> 总体 `fail`
   - 无 `fail` 且存在 `hold` -> `runtime_gate_state=hold` 且对外 `gate_decision=fail`（进入 HOLD 治理）
   - 其余 -> 总体 `pass`

## Fail-Closed 规则（无硬超时）

默认失败触发：

1. 证据缺失或不可追溯。
2. 判定结果不可解析。
3. 关键输入缺失（Objective/Spec/Output）。

补充规则：

1. 长时运行不是失败条件。
2. `hold -> fail` 仅在 HOLD 治理确认异常或无进展证据时触发。
3. `test_invalid` 仅用于编译期和运行前契约错误。
4. `hold` 只允许出现在 `runtime_gate_state`，不允许作为对外发布结论枚举。

## Profile 治理

1. 采用“统一核心协议 + 模块级 profile”模式。
2. 全模块共享 baseline profile，模块只覆盖差异。
3. profile 仅允许调整：grader 组合、轮次、重试、证据附加项。
4. 以下条款不可被 profile 覆盖：
   - `gate_decision` 枚举
   - `runtime_gate_state` 枚举
   - Unified Verdict 必填字段
   - Fail-Closed 主规则
5. profile 采用语义化版本并登记 registry。

## 依赖关系（类型化）

1. 依赖 `M2`（`R/E`）：运行状态机、调度与证据回写。
2. 依赖 `M4`（`R`）：生命周期状态推进与审查消费。
3. 依赖 `M6`（`E`）：对齐施工面阶段目标和验收纪律。

## 关键复用关系

1. `M3` 复用 `M1` 作为开发闭环门禁。
2. `M4` 复用 `M1` 作为 lifecycle-review 的测试输入。
3. `M5` 复用 `M1` 验证自进化改进效果。

## Thread-3 运行闭环补充（2026-02-22）

1. 新增测试入口：`tests/m1-runtime/run_post_dev_regression.py`。
2. 用例覆盖：
   - `TC-M1-CHAIN-001`：`M3 -> M1 -> M4` pass 主链路。
   - `TC-M1-CHAIN-002`：关键输入缺失触发 `test_invalid/fail-closed`，并阻断 lifecycle transition。
   - `TC-M1-CHAIN-003`：`evaluation hold -> hold-governance` 路由并产出 `hold_resolution_ref`。
   - `TC-M1-CHAIN-004`：`M5` 最小接入 `M1` 门禁入口可执行。
3. round 证据目录：`runtime_data/execution/evidence/quality-gate/runtime-validation-round-6-m1-closure/`。

## 真实服务语义补测（2026-02-22）

1. 新增主流程用例入口：`tests/m1-runtime/run_semantic_service_validation.py`。
2. 用例目标（第一优先级）：
   - `TC-M1-SERVICE-001`：`hr` 提交真实产品需求 -> `qa` 产出测试设计 -> `LLM-Judge` 评估 mock 交付 -> `qa` 输出缺陷与 debug 建议。
3. 运行约束：
   - 评测方法必须为 `LLM-Judge`，禁止退化为字段匹配式 Rule Match。
   - 对 mock 交付必须产生阻断判定（`fail` 或 `hold`），禁止“形式通过”。
   - 缺陷与 debug 建议必须非空并可追溯证据路径。
4. round 证据目录：`runtime_data/execution/evidence/quality-gate/runtime-validation-round-8-semantic-service/`。

## 验收清单

- [ ] `gate_decision` 对发布路径具有真实阻断效果
- [ ] `M3/M4/M5` 均复用统一门禁且无重复评测引擎
- [ ] Unified Verdict 满足必填字段与白名单约束
- [ ] `TEST.md -> datapoint` 编译错误可返回 `test_invalid` 并阻断
- [ ] 证据包可被 `M2/M4` 追溯消费
- [ ] 评测链路连续：准备 -> 实现 -> 评测
- [ ] HOLD triage 可执行（continue/retry/debug/fail）
