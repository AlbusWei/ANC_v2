# M3 — 反身自开发模块详细设计

> 版本: v0.7.0 | 建设优先级: P1 | 最后更新: 2026-02-23

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
2. `M3` 可在 `draft` 级开发先行；本轮状态收敛上限为 `review`，且进入 `review` 前必须通过 `M4`。
3. `M3` 必须复用 `M1` 的测试与门禁，不得重复实现评测引擎。
4. `M3` 只定义开发型流程与技能，不承担触发策略治理（`M2/M4` 负责）。

## 组件与落盘状态

| 组件 | 目标流程/技能资产 | 状态 |
|---|---|---|
| minimal loop | `development-process` | 已落盘（review） |
| internal productization loop | `full-development` | 本轮新增（review） |
| emergency path | `hotfix` | 本轮新增（review） |
| structural change path | `refactor` | 本轮新增（review） |
| objective authoring | `meta.arch.objective-writer` | 本轮新增（review） |
| agent asset creation | `meta.arch.agent-creator` | 本轮新增（review） |
| process asset creation | `meta.arch.process-creator` | 本轮新增（review） |
| schema/template gate | `meta.arch.template-validator` | 本轮新增（review） |
| skill asset creation | `meta-skill-creator`（`skill-creator` 仅历史别名） | 本轮纳入注册（review） |

## P5 子流程调用映射（Phase4 补齐）

1. `objective-scope-baseline`：由 `full-development.p1`、`refactor.p1` 调用，负责 Objective/Scope 基线收敛。
2. `hotfix-intake-normalization`：由 `hotfix.p1` 调用，负责紧急修复入口归一与回滚方向约束。
3. `hotfix-scope-spec-baseline`：由 `hotfix.p2` 调用，负责 hotfix 场景 scope/spec 组合闭合。
4. `spec-authoring-contract`：由 `full-development.p2`、`refactor.p2` 调用，负责规格产物契约化。
5. `implementation-execution-core`：由 `full-development.p4`、`hotfix.p4`、`refactor.p4` 调用，负责实现执行核心链路。
6. `release-packaging-governed`：由 `full-development.p7`、`hotfix.p7` 调用，负责发布打包与回滚包治理。
7. `evolution-feedback-planning`：由 `full-development.p8` 调用，负责反馈闭环与演化规划。

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
2. 汇合门：`M3` 新资产推进到 `review` 前必须通过 `M4` 审批链。
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
缓解：坚持“`M3 draft` 先行，本轮仅收敛到 `review`，`active` 延后”硬门禁。
2. 风险：流程资产新增后文档/registry 不一致。  
缓解：同回合执行 layer/module 联动门禁（设计文档 + inventory + registry + 施工平面）。
3. 风险：开发型流程违反连续性约束。  
缓解：拆分断点前后流程并由上级流程编排，禁止顺序链硬拼。

## 验收矩阵（Session2 设计闭合版）

| 验收 ID | 验收条目 | 验证命令 | 证据路径 | 通过判据 | 失败判据 |
|---|---|---|---|---|---|
| M3-AC-01 | 三主流程文档具备治理绑定蓝图（`process_type + governance_bundle`） | `rg -n "process_type|governance_bundle" docs/design/processes/{full-development-process.md,hotfix-process.md,refactor-process.md}` | `docs/design/processes/full-development-process.md`<br>`docs/design/processes/hotfix-process.md`<br>`docs/design/processes/refactor-process.md` | 三份文档都命中 `process_type` 与 `governance_bundle` 固定值 | 任一文档缺失字段或语义不一致 |
| M3-AC-02 | `registry-sync/escalation` 设计文档闭合（含输入/输出/Fail-Closed/test_mount/生命周期） | `rg -n "输入契约|输出契约|Fail-Closed|test_mount|生命周期" docs/design/processes/{registry-sync-process.md,escalation-process.md}` | `docs/design/processes/registry-sync-process.md`<br>`docs/design/processes/escalation-process.md` | 两份文档均命中全部契约关键字 | 缺任一关键字段即不通过 |
| M3-AC-03 | M3 技能包补齐系统治理依赖技能接口 | `rg -n "impact-analyzer|release-manager|系统治理依赖技能" docs/design/skills/{system-skills.md,self-development-skills.md}` | `docs/design/skills/system-skills.md`<br>`docs/design/skills/self-development-skills.md` | 两个技能定义卡字段完整且生命周期收敛到 `review`（不推进 `active`） | 仅出现名称、未出现契约字段 |
| M3-AC-04 | `release-manager-agent` 达到可运行资产口径（设计） | `rg -n "bound_skills|participating_processes|release_request_in|release_delivery_out|release_reject_out|Fail-Closed|test_mount" docs/design/agents/app/delivery/release-manager-agent.md` | `docs/design/agents/app/delivery/release-manager-agent.md` | 输入/成功输出/拒绝输出三类契约均完整 | 缺少任一输出结构或 Fail-Closed 路径 |
| M3-AC-05 | OpenSpec 与 gap 基线对齐且可校验 | `openspec validate m3-self-development-e2e-online --json` | `openspec/changes/m3-self-development-e2e-online/design.md`<br>`openspec/changes/m3-self-development-e2e-online/tasks.md`<br>`openspec/changes/m3-self-development-e2e-online/m3-gap-baseline.md` | validate 返回 `valid=true` 且 Session2 条目状态一致 | validate 失败或文档状态冲突 |
| M3-AC-06 | registry 契约门禁通过（设计层联动无破坏） | `python3 shared/registry/registry_contract_tool.py verify` | `shared/registry/*.json`（只读门禁） | verify 通过且无 contract/projection 破坏 | verify 非零退出或契约报错 |

说明：

1. Session2 只验设计闭合，不宣称运行资产可执行。
2. Session3 才进入 `skills/processes/agents` 目录级实现与 registry 实条目落地。
