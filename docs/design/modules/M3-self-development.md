# M3 — 反身自开发模块详细设计

> 版本: v0.5.0 | 建设优先级: P1 | 最后更新: 2026-02-21

## 模块定位

`M3` 是 ANC v2 的反身自开发执行层，负责将“开发系统自身资产”的需求转化为可调度、可门禁、可审计的流程实例。

相关文档：

1. `docs/design/processes/full-development-process.md`
2. `docs/design/processes/hotfix-process.md`
3. `docs/design/processes/refactor-process.md`
4. `docs/design/skills/self-development-skills.md`
5. `docs/design/processes/development-loop-core-standard.md`

## Phase 1 成功优先级

1. 流程可执行：`full-development/hotfix/refactor` 形成可调度资产并完成 registry 落盘。
2. 连续性闭合：开发断点前后流程拆分与上级编排满足新增硬约束。
3. 门禁真实生效：`M1` gate 决策可阻断 `M3 -> M4` 生命周期推进。
4. 双主线复用稳定：内部主线与外部交付主线复用同一 M3 能力，不出现旁路。

## 模块边界

1. `M3` 只负责开发执行闭环，不负责生命周期状态裁决。
2. `M3` 可在 `draft` 级开发先行，进入 `review/active` 必须通过 `M4`。
3. `M3` 必须复用 `M1` 的测试与门禁，不得重复实现评测引擎。
4. `M3` 只定义开发型流程与技能，不承担触发策略治理（`M2/M4` 负责）。

## 组件与落盘状态

| 组件 | 目标流程/技能资产 | 状态 |
|---|---|---|
| minimal loop | `development-process` | 已落盘（draft） |
| internal productization loop | `full-development` | 本轮新增（draft） |
| emergency path | `hotfix` | 本轮新增（draft） |
| structural change path | `refactor` | 本轮新增（draft） |
| objective authoring | `meta.arch.objective-writer` | 本轮新增（draft） |
| agent asset creation | `meta.arch.agent-creator` | 本轮新增（draft） |
| process asset creation | `meta.arch.process-creator` | 本轮新增（draft） |
| schema/template gate | `meta.arch.template-validator` | 本轮新增（draft） |
| skill asset creation | `skill-creator` | 本轮纳入注册（draft） |

## 流程连续性模型

1. 开发前连续段：`quality-gate-preparation`（AP-005/018/019）。
2. 开发执行断点：`AP-006 implementation-execution`。
3. 开发后连续段：`quality-gate-evaluation`（AP-007/008/009/020）。
4. 生命周期治理段：`AP-010/011` 由 `M4` 执行。
5. 连续性约束：单复合流程不跨非连续生命周期段；跨断点通过上级流程显式编排。
6. phase 闭合约束：每个 phase 必须映射到已定义 AP 或已定义复合子流程。

## 输入契约（统一开发任务包）

1. `objective_ref`
2. `scope_baseline_ref`
3. `spec_ref`
4. `test_doc_ref`
5. `change_type`（`full-development|hotfix|refactor`）
6. `risk_level`
7. `lifecycle_target`

## 输出契约（统一交付包）

1. `implementation_ref`
2. `final_gate_verdict_ref`
3. `lifecycle_transition_ref`
4. `registry_sync_ref`
5. `release_package_ref`（可选，按 O7 义务触发）
6. `m3_evidence_bundle_ref`

## 依赖关系（类型化）

1. 依赖 `M2`（`R/E`）：流程编排、实例状态、证据归档与升级链执行。
2. 依赖 `M1`（`T`）：Objective/Spec/Test 门禁与回归判定。
3. 依赖 `M4`（`G`）：生命周期审批、registry 同步与状态迁移。
4. 依赖 `M6`（`E`）：里程碑对齐、风险登记与施工纪律。

## 与 M4 的并行策略

1. 并行原则：`M3` 与 `M4` 可并行建设。
2. 汇合门：`M3` 新资产推进到 `review/active` 前必须通过 `M4` 审批链。
3. 禁止项：未过 `M4` 门禁的资产不得标记为可发布。

## 双主线复用约束

1. 内部产品主线直接消费 `full-development`。
2. 外部交付主线在 `delivery-iterations` 阶段必须复用 `M3` 流程闭环。
3. 任意交付路径均不得跳过 `M1` 门禁与 `M4` 生命周期治理。

## Fail-Closed 规则

1. Objective/Spec/Test 任一断链，拒绝进入实现阶段。
2. phase 映射不闭合或引用流程不可达，拒绝流程实例启动。
3. `gate_decision` 为 `fail|hold|test_invalid` 且未完成治理回填，拒绝进入 lifecycle 阶段。
4. lifecycle 证据缺失，拒绝状态迁移并升级 `actor -> owner -> bpm -> admin -> human`。
5. 外部交付流程绕过 `M3` canonical 流程时直接阻断。

## 风险与缓解

1. 风险：`M3/M4` 并行建设导致边界漂移。  
缓解：坚持“`M3 draft` 先行，`review/active` 必经 `M4`”硬门禁。
2. 风险：流程资产新增后文档/registry 不一致。  
缓解：同回合执行 layer/module 联动门禁（设计文档 + inventory + registry + 施工平面）。
3. 风险：开发型流程违反连续性约束。  
缓解：拆分断点前后流程并由上级流程编排，禁止顺序链硬拼。

## 验收清单

- [ ] `full-development/hotfix/refactor` 已注册并可被 BPM 调度
- [ ] M3 核心技能已注册且具备 Capability Contract + test_mount
- [ ] `M1` gate 失败可真实阻断 `M3 -> M4`
- [ ] 外部 `delivery-iterations` 复用路径无旁路
- [ ] 连续性约束与 phase 闭合约束通过文档与 manifest 双重校验
