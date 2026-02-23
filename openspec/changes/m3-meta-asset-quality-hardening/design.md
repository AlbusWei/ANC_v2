## Context

本 change 在 `m3-self-development-e2e-online` 并行推进阶段启动，目标是先补齐 Meta 资产质量与流程架构问题，再作为 Session5/6 的前置治理门禁。

关键事实：

1. 历史包装流程（`ap-*-bundle`）与 AP 原子语义不一致，存在职责重叠与可维护性问题。
2. Meta 资产已有基本骨架，但“运行级可用性”和“工程化复用性”不足。
3. QA 体系已可运行，具备把在线行为作为主验收的前提。
4. 本文档中出现 `ap-*-bundle` 仅用于“历史迁移说明”；目标态与运行态只使用现行 P5 子流程术语。

## Goals / Non-Goals

### Goals

1. 基于历史迁移矩阵完成 `bundle -> P5` 替换，并在主流程中完成调用迁移。
2. 升级 Meta 技能与 Meta 流程资产质量到 `review` 准入线。
3. 建立 QA 在线测试主验收机制，覆盖 openclaw runtime 效果。
4. 完成 OpenSpec/design/inventory/registry/construction-plane 联动闭合。

### Non-Goals

1. 本轮不推进任何资产到 `active`。
2. 不在本轮扩展非 Meta 范围的大规模业务功能。
3. 不修改历史证据快照，仅增补映射与说明。

## Decisions

### Decision A: 彻底淘汰历史 `ap-*-bundle`，改为 P5 子流程库（历史迁移说明）

1. 原 `ap-*-bundle` 仅作为历史兼容信息，不再作为目标态运行资产。
2. 主流程（`development-process/full-development/hotfix/refactor`）统一改为调用 P5 子流程。
3. 迁移状态流固定为“同回合 `deprecated -> retired`”，不采用“直接 retired”捷径。
4. 在 P2 实施完成前，bundle 只能存在于迁移矩阵与兼容说明，不得作为目标架构描述。

### Decision B: 流程拆分方法论采用“MECE + 金字塔 + 设计原则”组合约束

#### B1 结构原则

1. **MECE**：子流程职责互斥、覆盖完整，禁止语义交叉。
2. **金字塔原理**：先结论后展开，先业务目标层再实现细节层。
3. **单一职责**：每个子流程只对一类治理结果负责。
4. **DIP**：主流程依赖契约，不依赖具体技能脚本细节。
5. **LoD**：流程节点仅与直接依赖交互，不跨层串联内部细节。
6. **组合/聚合复用**：通过子流程组合复用，而非复制 phase 链。

#### B2 反例（禁止）

1. 同一子流程同时承担“需求归一 + 规格编排 + 发布打包”。
2. `process_id` 粒度仅按历史 AP 编号拼接，未体现职责边界。
3. 父流程直接跨两层引用底层技能，绕过中间契约。
4. 不同主流程共享一段“半重叠”子流程而不声明变体契约。

#### B3 AP 合并策略（冻结）

1. 采用“避免重叠优先”：先确保 AP 语义边界不重叠，再考虑流程数量优化。
2. 若 AP 合并引发语义重叠，不合并 AP 语义，在 P5 组合层解耦。
3. 任何一对多/多对多责任映射若无“重叠解释 + 解耦策略”，按 Fail-Closed 阻断。

### Decision C: 冻结历史 bundle -> P5 迁移矩阵（Phase1 产物）

| 待淘汰 bundle | 替代 P5 子流程 ID | AP 语义边界 | 输入契约 | 输出契约 | 调用方流程 | 迁移顺序 | 兼容期与退役策略 | 重叠解释/解耦说明 |
|---|---|---|---|---|---|---|---|---|
| `ap-004-bundle` | `spec-authoring-contract` | AP-004 | `objective_ref`, `scope_baseline_ref` | `spec_ref` | `full-development.p2`, `refactor.p2` | 1 | 同回合 `deprecated -> retired` | 作为唯一规格产出语义，禁止被其它子流程内联重写 |
| `ap-006-bundle` | `implementation-execution-core` | AP-006 | `spec_ref`, `test_plan_ref` | `implementation_ref` | `full-development.p4`, `hotfix.p4`, `refactor.p4` | 2 | 同回合 `deprecated -> retired` | 只负责实现执行，不承载验证/发布语义 |
| `ap-012-bundle` | `release-packaging-governed` | AP-012 | `candidate_artifacts_ref`, `final_gate_verdict_ref`, `lifecycle_transition_ref`, `registry_sync_ref` | `release_package_ref`, `changelog_ref`, `release_decision`, `rollback_bundle_ref` | `full-development.p7`, `hotfix.p7` | 3 | 同回合 `deprecated -> retired` | 发布语义独占，禁止与演化规划混合 |
| `ap-001-002-bundle` | `hotfix-intake-normalization` | AP-001 + AP-002（hotfix profile） | `incident_context_ref` | `hotfix_objective_ref`, `impact_scope_ref`, `rollback_direction_ref` | `hotfix.p1` | 4 | 同回合 `deprecated -> retired` | 与通用 intake 的重叠通过 incident profile 隔离 |
| `ap-001-002-003-bundle` | `objective-scope-baseline` | AP-001 + AP-002 + AP-003（normal/refactor profile） | `objective_context_ref` | `objective_ref`, `scope_baseline_ref` | `full-development.p1`, `refactor.p1` | 5 | 同回合 `deprecated -> retired` | 与 hotfix intake 的 AP-001/002 重叠由 profile + 调用方边界解耦 |
| `ap-013-014-015-017-bundle` | `evolution-feedback-planning` | AP-013 + AP-014 + AP-015 + AP-017 | `feedback_evidence_ref` | `improvement_plan_ref`, `retro_report_ref` | `full-development.p8` | 6 | 同回合 `deprecated -> retired` | 仅演化反馈，不承载发布/生命周期迁移 |
| `ap-003-004-bundle` | `hotfix-scope-spec-baseline` | AP-003 组合 `spec-authoring-contract`（AP-004 不重复定义） | `hotfix_objective_ref`, `impact_scope_ref` | `hotfix_scope_baseline_ref`, `hotfix_spec_ref` | `hotfix.p2` | 7 | 同回合 `deprecated -> retired` | 通过组合层解耦 AP-004，避免与 `spec-authoring-contract` 语义重叠 |

### Decision D: 验证策略“QA 在线优先，静态门禁兜底”

1. 主验收：openclaw 运行时在线用例结果。
2. 基础门禁：`registry_contract_tool.py verify`、`openspec validate`。
3. 若在线测试与静态校验结论冲突，以在线行为问题优先阻断。

### Decision E: 生命周期策略固定到 `review`

1. 本轮整改资产可从 `draft -> review`。
2. `review -> active` 明确延后到后续观测窗口与回滚演练回合。

### Decision F: Phase1 完成判据（新增）

1. 历史迁移矩阵覆盖全部 7 个 bundle，且逐行具备 I/O、调用方、顺序、退役策略。
2. 不存在未解释的一对多/多对多责任重叠。
3. 所有目标文档明示 bundle 非目标态。

### Decision G: 流程协作骨架修正策略（新增）

1. AP 穿透策略采用 `1B`：允许“同 Actor + 低风险 + 迁移窗口”场景临时直调 skill，但必须标注 `ap_bypass_reason` 与迁移计划。
2. 会话粒度采用 `2A`：phase 级 isolated session，避免多 phase 累积在主会话导致上下文污染。
3. 迭代策略采用“先跑后补”：优先验证协作主目标可运行，再按运行暴露问题补充契约细节。
4. 首个试点固定为 QA 主线：`quality-gate-evaluation`。
5. 表达策略采用 `A`：自然语言上下文是一等输入，结构化契约作为增强层，不反客为主。
6. 修正计划文档：`openspec/changes/m3-meta-asset-quality-hardening/process-collaboration-skeleton-v1-plan.md`。

### Decision H: 协作骨架扩展策略（新增）

1. 真实分发要求：`isolated session` 必须落在 OpenClaw 真实会话上，不接受“仅本地模拟分发”。
2. 扩展顺序：先扩 `full-development`，再扩 `hotfix/refactor`。
3. AP 迁移策略：按流程顺序推进，不做风险分层。
4. `full-development` 试点要求：
   - 每个 phase 执行真实 `openclaw` 分发；
   - 同 actor 跨 phase 通过 `sessions.reset` 强制新会话；
   - 会话 ID 必须可核对。

## Phase Plan (P0~P9)

### P0 初始化与规格落盘

1. 固化变更边界、写全 OpenSpec 与线程计划。
2. 把 P1~P7 输入/输出/DoD/门禁命令一次落盘。

### P1 方法论与迁移蓝图

1. 增补流程拆分标准文档。
2. 形成历史 bundle -> P5 子流程映射矩阵（仅用于追溯说明）。

### P2 流程重构实现

1. 新增 P5 子流程资产。
2. 主流程切换调用并去除历史 bundle 运行引用。

### P3 Meta 技能质量升级

1. 升级 8 个 Meta 技能。
2. 解决本地 `skill-creator` 与 managed 同名冲突。

### P4 全量联动

1. 设计文档、inventory、registry、construction plane、OpenSpec 一致性闭合。

### P5 QA 在线测试基座强化

1. 建立 Meta 资产专项在线测试编排与证据结构。

### P6 在线执行与缺陷闭环

1. 按 QA 流程执行 online suite、修复、回归。

### P7 收口

1. 四向对账与生命周期收敛到 `review`。
2. Entire 会话闭环与审计信息确认。

### P8 流程协作骨架试点（新增）

1. 在 `quality-gate-evaluation` 落地 phase 级协作骨架与 isolated session 分发。
2. 验证“多 Agent/多会话协作”主目标可运行，再扩展到其他主流程。

### P9 full-development 协作扩展（新增）

1. 在 `full-development` 落地协作骨架语义字段与运行级 runner。
2. 通过 `process-instance-manager` 执行真实 openclaw 分发，并在 phase 前执行会话 reset。
3. 补充运行级用例，验证 8 phase 分发、会话一致性与同 actor 隔离。

## Fail-Closed / Rollback Strategy

每个 phase 的统一失败回退策略：

1. **P0/P1 失败**：停止实现型工作，回退到规格修订。
2. **P2 失败**：停止状态迁移，恢复主流程到上一个可运行 manifest 快照。
3. **P3 失败**：阻断技能状态推进，保留原条目并记录冲突映射。
4. **P4 失败**：阻断合入，补齐联动文档与 registry 一致性后重试。
5. **P5/P6 失败**：在线 case 未通过视为不可发布，继续缺陷闭环。
6. **P7 失败**：禁止宣告完成，直到四向对账与 trailer 校验通过。
7. **P8 失败**：禁止扩散到其它流程，先在 QA 试点内完成最小可运行闭环。
8. **P9 失败**：禁止扩散到 `hotfix/refactor`，先在 `full-development` 修复分发/会话一致性。

## Risks & Mitigations

1. 风险：bundle 迁移导致主流程短期不可运行。
   - 缓解：分批迁移 + 每批运行门禁 + 保留可回滚快照。
2. 风险：子流程拆分过细或过粗导致复用失衡。
   - 缓解：以 MECE + SRP 做拆分评审，并在反例清单中强约束。
3. 风险：在线测试环境波动导致误判。
   - 缓解：保留静态门禁与二次回归窗口，按证据判定。

## Open Questions

1. AP 旁路的迁移窗口按“回合”还是“日期”收敛，待 full-development 试点运行数据后固化。
2. phase 自然语言上下文包是否统一模板，待 `full-development/hotfix/refactor` 三条主流程首轮运行后决定。
