# SSOT Design — Superpower + OpenJudge SDD/TDD Governance (OpenSpec Removed)

> Status: Active SSOT
> Last Updated: 2026-03-03
> Scope: Superpower 协同契约 + OpenJudge 执行门禁 + M1/M3/M4/M5/M6 联动 + M5 owner 运营闭环详细设计

## 1) 权威范围

本文件是该主题唯一设计真相（design SSOT）。

Supersedes:
- `docs/plans/archive/2026-02-27-m1-m3-gate-authenticity-design.md`
- `docs/plans/archive/2026-03-01-m4-m5-productized-design.md`
- `docs/plans/archive/2026-03-01-m1-m3-m4-m5-executable-gap-closure-design.md`
- 所有以 OpenSpec 为主协同入口的历史设计结论

## 2) 背景与问题

当前体系虽然已具备 M1 OpenJudge 适配与质量门禁能力，但在协同契约层仍存在 OpenSpec 依赖，导致：

1. 协同契约源不唯一（Superpower 与 OpenSpec 并存）。
2. SDD 产物与 TDD 门禁输入未被同一契约主键绑定。
3. 施工回合（M6）在 process/skill/schema 层仍以 OpenSpec 字段为必填，形成语义与执行漂移。

本轮目标是**完全移除 OpenSpec 主链依赖**，以 Superpower 作为唯一协同与决策契约层，并通过 M1(OpenJudge) 实现可执行 TDD 门禁。

## 3) 目标终态架构

唯一主链：

`Superpower Contract -> M3(SDD execution) -> M1(OpenJudge TDD Gate) -> M2(runtime state) -> M4(lifecycle governance)`

### 3.1 各层职责

1. Superpower：唯一设计/计划/决策协同契约源（替代 OpenSpec）。
2. M3：按 superpower 契约实施开发（SDD 执行层）。
3. M1：使用 OpenJudge 作为评测执行内核，输出统一 gate verdict（TDD 门禁层）。
4. M2：运行态状态机与过程治理。
5. M4：产品版本实例生命周期状态迁移与角色切换。

### 3.2 强制输入绑定

1. SDD 运行上下文必须产出 `superpower_ref`。
2. TDD 门禁必须消费 `superpower_ref + TEST.md 编译产物 + actual outputs`。
3. 若 `superpower_ref` 缺失、不可解析或不可追溯，门禁默认 fail-closed。

## 4) 关键设计决策（Decision Baseline）

### D1. 完全替代（No Compatibility）
OpenSpec 不保留兼容路径，不再作为主流程输入/输出字段、门禁验证命令、回合同步协议来源。

### D2. 协同契约单源
Superpower 是唯一协同契约源；任何流程输入中的协同引用字段统一为 `superpower_ref`。

### D3. 同步记录单源
施工治理回合同步输出统一为 `superpower_sync_ref`；旧 `openspec_sync_ref` 语义废止。

### D4. SDD+TDD 联动硬约束
SDD 的交付必须可被 TDD 门禁反查；缺失 SDD 契约上下文的 TDD 请求一律拒绝。

### D5. OpenJudge 角色固定
OpenJudge 仅负责 raw eval 执行，M1 adapter 负责 unified verdict 与 gate_decision 归一。

### D6. Fail-Closed 默认策略
证据缺失、契约缺失、判定不可解析、指标不可比、回滚缺失、非法迁移均阻断。

### D7. 最小可执行与可审计
优先保证“可执行闭环 + 可追溯证据 + 阻断真实生效”，再考虑优化与扩展。

## 5) 资产级设计改造范围

### 5.1 必改流程资产

1. `processes/meta/construction-plane-governance/process.json`
   - `openspec_ref -> superpower_ref`
   - `openspec_sync_ref -> superpower_sync_ref`
   - p4 phase 改为 `sync-superpower-state`
2. `processes/meta/construction-plane-governance/SKILL.md`
3. `processes/meta/construction-plane-governance/PROCESS.md`

### 5.2 必改技能资产

1. 新增 `skills/system/superpower-sync/*`
2. 从主链移除 legacy 协同占位资产引用（仅保留 `system.integration.superpower-sync`）。

### 5.3 必改接口/模型资产

1. 新增 `docs/design/interfaces/superpower-collaboration-protocol.md`
2. 新增 `docs/design/data-models/superpower-collaboration-schema.json`
3. 新增 `docs/design/processes/atomic/AP-035-superpower-round-sync.md`
4. 旧 openspec 协同协议、schema、AP 标记 superseded 并摘除主链引用

### 5.4 必改 SDD/TDD 门禁资产

1. `docs/design/modules/M1-openjudge-adapter-spec.md`
2. `docs/design/modules/M1-test-system.md`
3. `docs/design/skills/quality-gate-skills.md`
4. `docs/design/skills/self-development-skills.md`
5. `processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py`
6. `tests/m1-runtime/run_post_dev_regression.py`

### 5.5 必改治理与验证资产

1. `shared/registry/registry_contract_tool.py`
2. `tests/m6-governance/run_post_dev_regression.py`
3. `tests/m2-bpm-runtime/run_tc_full_dev_proc.py`
4. `skills/system/construction-audit/scripts/construction_audit.py`
5. `processes/meta/construction-plane-governance/scripts/run_round.py`
6. `processes/meta/construction-plane-governance/scripts/round_evidence_tool.py`

### 5.6 必改索引与施工平面资产

1. `docs/design/inventories/process-inventory.md`
2. `docs/design/inventories/skill-inventory.md`
3. `docs/design/modules/module-dependency-matrix.md`
4. `docs/architecture/construction_plane.md`

### 5.7 已完成的模块级对齐（2026-03-01）

1. `docs/design/modules/M3-self-development.md`
   - 输入契约加入 `superpower_ref` 必填。
   - 输出契约加入 `superpower_sync_ref`，并要求证据包可追溯到 `superpower_ref + superpower_sync_ref`。
   - Fail-Closed 明确 `superpower_ref` 缺失/不可解析/不可追溯时阻断。
   - 验收口径去 OpenSpec 化（`M3-AC-05` 改为 superpower 会话工件与上下文注入契约校验）。
2. `docs/design/modules/M4-lifecycle-management.md`
   - 语义切换为 `ProductVersionInstance` 生命周期迁移与版本角色切换治理。
   - lifecycle-review 输入契约加入 `superpower_ref`。
   - 明确与 registry 资产 5 态并存，不替代。
3. `docs/design/modules/module-dependency-matrix.md`
   - `M3 + M4 -> M5` 汇合门加入 `superpower_ref` 追溯闭环约束。

## 6) In Scope / Out of Scope

### In Scope

1. OpenSpec -> Superpower 完全替代（主链字段、流程、技能、校验）。
2. SDD 与 TDD 的契约主键绑定（`superpower_ref`）。
3. M1 门禁对缺 `superpower_ref` 的 fail-closed。
4. M6 施工回合同步记录与 schema 改造。

### Out of Scope（本轮）

1. 新增复杂平台服务层。
2. 非必要 UI 层治理界面。
3. 与当前主题无关的模块重构。

## 7) 验收设计口径

1. 主流程中不存在 `openspec_ref/openspec_sync_ref`。
2. `system.integration.superpower-sync` 成为唯一回合同步技能入口。
3. M1 gate 对缺 `superpower_ref` 请求 fail-closed。
4. SDD 输出和 TDD 输入通过 `superpower_ref` 可追溯绑定。
5. registry 与回归验证通过，且无 OpenSpec 主链依赖残留。

## 8) 设计变更日志

- 2026-03-01：重写为“Superpower 完全替代 OpenSpec”的单源设计基线。
- 2026-03-01：完成 M3/M4 模块文档与依赖矩阵对齐，补齐 `superpower_ref/superpower_sync_ref` 追溯与 fail-closed 口径。
- 2026-03-03：新增 M5 自进化 owner 运营闭环详细设计（对象模型、流程机制、门禁与分阶段落地）。

## 9) M5 自进化 Owner 运营闭环详细设计（2026-03-03）

### 9.1 问题定义（As-Is）

现状具备以下基础能力：

1. `M2` 触发运行时（schedule/event）已可执行。
2. `M1` 门禁（含 hold 治理与 auto-retest）已可执行。
3. `M3` 开发主链与 `evolution-feedback-planning` 子流程已可执行。
4. `M4` 生命周期治理流程 `lifecycle-review` 已可执行。

但仍缺少“资产 owner 持续运营闭环”的关键机制：

1. owner 多停留在 registry 字段，缺可执行责任契约与运营节奏。
2. `EvolutionProposal` 尚未作为统一运行对象落盘与流转。
3. L4 设计中的 monitor/analyst/planner、演化技能族、演化流程族未形成注册可执行集合。
4. `M5 -> M3 -> M1 -> M4` 的端到端提案闭环未形成专属回归门禁。

### 9.2 目标态（To-Be）

构建“每个资产有 owner、owner 有运营责任、责任可执行可考核”的自进化系统：

1. 每个资产必须绑定 `owner_agent_id` 与运营契约（目标、指标、节奏、回滚策略）。
2. 资产运行信号进入统一提案模型 `EvolutionProposal`，由治理流程排序与放行。
3. 提案执行必须串联 `M3 实施 -> M1 验证 -> M4 迁移`，任一环证据不足即 Fail-Closed。
4. `review -> active` 不再只依赖单次门禁通过，必须满足观测窗口与回滚演练准入。

### 9.3 设计原则

1. 因果链固定：`运行信号 -> 问题识别 -> 提案 -> 实施 -> 验证 -> 迁移 -> 复盘`。
2. owner 问责显式化：无 owner、无节奏、无指标的资产不得宣告“可运营”。
3. 双状态机并存：registry 资产 5 态与 `ProductVersionInstance` 生命周期并存，互不替代。
4. Fail-Closed 优先：证据不可达、指标不可比、回滚缺失、越权迁移一律阻断。
5. 先最小可执行后专职化：先复用现有 actor/流程跑通闭环，再引入专职演化 agent/skill。

### 9.4 目标态闭环架构

统一闭环：

`Observe -> Diagnose -> Propose -> Govern -> Implement -> Verify -> Transition -> Observe`

模块责任：

1. `M5`：Observe/Diagnose/Propose/Govern（提案生产与治理编排）。
2. `M3`：Implement（按提案执行变更）。
3. `M1`：Verify（产出门禁 verdict 与异常治理证据）。
4. `M4`：Transition（状态迁移与版本角色切换）。
5. `M6`：Evidence Plane（跨回合证据与追溯一致性）。

### 9.5 核心对象模型（新增）

#### A) `AssetOperationProfile`

用于把 owner 责任从“字段存在”升级为“运营契约存在”。

必填字段：

1. `asset_ref`
2. `owner_agent_id`
3. `service_goal`
4. `health_metrics`（最小 1 项）
5. `review_cadence`（周期策略）
6. `risk_level`
7. `rollback_policy_ref`
8. `active_admission_policy_ref`

Fail-Closed：

1. 缺 `owner_agent_id` 或 owner 不可解析。
2. `health_metrics` 为空或不可计算。
3. 缺 `rollback_policy_ref`。

#### B) `AssetHealthSnapshot`

必填字段：

1. `snapshot_id`
2. `asset_ref`
3. `window_start` / `window_end`
4. `metric_values`
5. `signal_level`（`normal|warning|critical`）
6. `evidence_refs`

Fail-Closed：

1. 时间窗口不可解析或逆序。
2. 指标缺基线不可比。

#### C) `AssetIssue`

必填字段：

1. `issue_id`
2. `asset_ref`
3. `detected_by`
4. `severity`
5. `owner_agent_id`
6. `status`（`open|triaged|planned|in_progress|verified|closed`）
7. `source_snapshot_ref`

#### D) `EvolutionProposal`（M5 主对象）

必填字段：

1. `proposal_id`
2. `trigger_type`（`periodic|event`）
3. `target_product_id`
4. `target_asset_refs`
5. `problem_statement`
6. `expected_value`
7. `verification_metrics`
8. `risk_assessment`
9. `rollback_plan_ref`
10. `owner_commitment_ref`

Fail-Closed：

1. `trigger_type` 非法。
2. `verification_metrics` 不可比。
3. 缺 `rollback_plan_ref`。
4. 缺 `owner_commitment_ref`（owner 未签收不得下发 M3）。

#### E) `EvolutionExecutionRecord`

必填字段：

1. `proposal_id`
2. `m3_execution_ref`
3. `m1_verification_ref`
4. `m4_transition_ref`
5. `final_decision`（`accepted|rejected|rolled_back`）

### 9.6 触发机制设计（周期 + 事件）

#### 周期触发（保底巡检）

1. 默认按 `review_cadence` 触发 owner 资产健康检查。
2. 触发输入：`AssetOperationProfile + 最近窗口 AssetHealthSnapshot`。
3. 输出：`AssetIssue` 或“无异常结论”。

#### 事件触发（插队治理）

触发条件（任一满足）：

1. `M1` 门禁连续失败超过阈值。
2. `hold` 比例或 `auto-retest` 失败率超阈值。
3. 关键 incident / 回滚事件发生。
4. 客户或业务反馈进入高风险分级。

输出要求：

1. 必须生成 `AssetIssue` 并绑定 owner。
2. 高风险事件必须在同回合形成 `EvolutionProposal` 或“拒绝提案+理由”。

### 9.6.1 与 OpenClaw Automation 机制适配（hooks / cron / heartbeat）

为保证本方案“可行且可运行”，M5 触发层必须与 OpenClaw 运行机制一一映射：

#### A) Hook（事件触发）适配

定位：M5 采用“双层 Hook 语义”，避免把 OpenClaw 平台事件误当作业务事件。

1. 平台层 Hook（OpenClaw 内置事件）：仅作为“外部输入/会话状态”桥接信号。
2. 领域层 Hook（ANC 自定义生命周期事件）：作为 M5 治理触发主信号源。

结论：M5 提案编排优先消费“领域层 Hook”，平台层 Hook 只负责把原始变化带入系统。

平台层 Hook（桥接）建议映射：

1. `message:received`：接入“原始输入”反馈与 incident 线索。
2. `message:transcribed` / `message:preprocessed`：接入“已处理内容”信号，避免在 Hook 内重复做媒体理解。
3. `command:new/reset/stop`：同步会话生命周期状态。
4. `gateway:startup` / `agent:bootstrap`：触发启动期自检与触发规则基线装载。

领域层 Hook（主触发）建议事件族：

1. `m1.gate.failed` / `m1.gate.hold` / `m1.gate.pass`。
2. `m3.implementation.failed` / `m3.implementation.completed`。
3. `m4.lifecycle.transition.approved` / `m4.lifecycle.transition.rejected` / `m4.lifecycle.rollback.executed`。
4. `m5.proposal.rejected` / `m5.proposal.accepted`（治理决策回流）。
5. `asset.health.degraded` / `asset.health.critical`（由周期巡检升级产生）。

领域层 Hook 最小契约（强制）：

1. `event_id`（幂等主键）
2. `event_name`（上述事件族之一）
3. `event_time`
4. `module`（`m1|m3|m4|m5|runtime-monitor`）
5. `asset_ref` / `target_product_id`
6. `severity`
7. `evidence_ref`
8. `owner_agent_id`（可解析到责任主体）
9. `dedupe_key`

执行约束（强制）：

1. Hook handler 必须“快返回”，遵循 `Filter Events Early`，禁止在 handler 内做重度分析。
2. 平台层 Hook 与领域层 Hook 一律先经 `sys.bpm.trigger-ingress-normalizer` 归一，再进入 `M2 trigger-event-runtime`。
3. Hook 不得直接绕过 `M5 -> M3 -> M1 -> M4` 门禁链路。
4. Hook handler 必须本地捕获并记录异常，禁止向外抛出导致其他 handler 被连带影响。
5. 领域层 Hook 缺 `evidence_ref`、`owner_agent_id` 不可解析或 `dedupe_key` 不可构造时，必须 Fail-Closed 并进入补数/升级链路。

#### B) Cron（精确定时）适配

定位：承接“精确时点”或“独立会话”任务。

两类运行模式：

1. `sessionTarget=main` + `payload.kind=systemEvent`
   - 适合需主会话上下文的提醒/信号注入。
   - 通过 `wakeMode` 控制 `now` 或 `next-heartbeat`。
2. `sessionTarget=isolated` + `payload.kind=agentTurn`
   - 适合重分析、低耦合后台任务、独立输出交付。
   - 可使用独立 `model/thinking`，避免污染主会话上下文。

调度约束：

1. `schedule.kind` 仅允许 `at|every|cron`。
2. `top-of-hour` 类表达式（示例：`0 * * * *`）默认可能进入确定性错峰窗口；对“必须整点准时”的任务显式设置 `schedule.staggerMs=0`（CLI `--exact`）。
3. 固定时点表达式（示例：`0 7 * * *`）按精确时刻执行；仅在显式配置 `staggerMs` 时引入偏移。
4. 需显式声明 `tz`（IANA 时区）避免跨环境时间偏移。
5. 复用 OpenClaw 默认重试/退避策略，不在 M5 侧重复实现第二套重试器。

#### C) Heartbeat（周期感知）适配

定位：承接“可批处理、上下文感知”的周期巡检。

适配原则：

1. 日常监控项优先进入 `HEARTBEAT.md` 批处理，而不是拆成多个 isolated cron。
2. Heartbeat 输出 `HEARTBEAT_OK` 时视为“本轮无可行动问题”，不强制生成提案。
3. 仅当触发阈值命中时，升级为 `AssetIssue -> EvolutionProposal` 链路。

#### D) Cron vs Heartbeat 选择规则（M5 固化）

1. 需要精确时间、一次性提醒、独立运行、模型覆写：用 Cron。
2. 需要上下文感知、多信号合并巡检、低噪声周期监控：用 Heartbeat。
3. 最佳实践：Heartbeat 负责常态感知，Cron 负责精确动作，Hook 负责事件入口。

### 9.6.2 M5 触发编排的 OpenClaw 最小实现蓝图

1. 周期巡检（常态）：
   - Heartbeat 执行 `asset-health-check` 检查单。
   - 若命中阈值，写入 `AssetIssue` 并触发 `trigger-event-runtime`。
2. 精确评审（治理）：
   - Cron（isolated）按周触发 `improvement-review`，输出优先级矩阵与提案草案。
3. 事件插队（异常）：
   - 平台层 Hook 仅做外部信号桥接；M1/M3/M4/M5 runner 在阶段结束时产出领域层 Hook 事件包。
   - 两类事件统一经 `trigger-ingress-normalizer -> trigger-event-runtime`，再升级为 `AssetIssue/EvolutionProposal`。
4. 主链执行（不变）：
   - `M5 proposal -> M3 implement -> M1 verify -> M4 transition`。

### 9.6.3 生命周期自定义 Hook 设计（重点补充）

为避免“平台事件语义与 ANC 工作流脱节”，M5 固化“流程节点产出领域事件”的实现口径：

领域事件产出锚点（必须）：

1. `quality-gate-evaluation` 结束时产出 `m1.gate.*`。
2. `full-development`（或实施流程）结束时产出 `m3.implementation.*`。
3. `lifecycle-review` 结束时产出 `m4.lifecycle.transition.*` / `m4.lifecycle.rollback.executed`。
4. `owner-evolution-governance` 评审阶段结束时产出 `m5.proposal.*`。

事件封装与分发规则（必须）：

1. 每个流程 runner 在“阶段完成点”写入领域事件包（同回合落盘）。
2. 事件包先进入 `trigger-ingress-normalizer`，统一生成 canonical trigger envelope。
3. 再由 `trigger-event-runtime` 执行匹配、去重、分发、证据归档、补数/升级。
4. 去重主键优先使用 `event_id`；缺失时回退到 `event_name + asset_ref + window_bucket + source_instance_id`。

事件升级规则（M5 固化）：

1. `m1.gate.failed` 连续超过阈值 -> 升级为 `asset.health.degraded`。
2. `m1.gate.hold` 超过 SLA -> 升级为 `asset.health.critical`。
3. `m4.lifecycle.rollback.executed` -> 直接升级 `critical` 并要求同回合 owner 审核。

Fail-Closed（领域 Hook 专项）：

1. 领域事件无 `evidence_ref`：拒绝进入提案链，仅进入补数/升级。
2. 领域事件无 `owner_agent_id`：拒绝升级为 `EvolutionProposal`。
3. 领域事件去重冲突不可判定：阻断分发并触发升级。
4. 领域事件未命中任何策略规则：不得静默丢弃，必须记录 `unmatched_event_receipt`。

### 9.7 流程机制设计（连续性 + phase 闭合）

#### P4：`owner-evolution-governance`（新增目标流程）

目标：把 owner 运营、提案治理、实施验证、迁移放行组织为单闭环治理流程。

阶段建议：

1. `p1 health-intake`：聚合 `AssetHealthSnapshot` 与 issue。
2. `p2 proposal-drafting`：形成 `EvolutionProposal`。
3. `p3 governance-review`：完成风险、回滚、owner 承诺审查。
4. `p4 implementation-dispatch`：下发 `M3`。
5. `p5 quality-verify`：调用 `M1`。
6. `p6 lifecycle-transition`：调用 `M4`。
7. `p7 retro-close`：回填指标对比与 owner 复盘。

#### P5 子流程族（新增目标）

1. `asset-health-check`
2. `evolution-proposal-governance`
3. `evolution-loop-orchestration`
4. `improvement-review`（与业务/系统双视角复盘）

#### 过渡态（本期可执行）

在专职演化资产未落地前，允许使用现有能力映射：

1. 观测与归因：`system-analyst + sys.arch.system-feedback-digest`
2. 提案与计划：`evolution-feedback-planning`
3. 实施：`full-development`（或 hotfix/refactor）
4. 验证：`quality-gate-evaluation`
5. 迁移：`lifecycle-review`

约束：该映射仅作为过渡执行路径，不替代目标态 L4 资产注册建设。

### 9.8 Owner 运营机制（新增）

#### A) Owner Accountability Contract（OAC）

每个 owner 必须签署并维护：

1. `服务目标`（价值主张）
2. `健康指标`（可比较、可复测）
3. `评审节奏`（周/双周）
4. `版本演进策略`（何时提案、何时冻结、何时回滚）
5. `异常处理 SLA`（分级响应窗口）

#### B) Owner Review Board（ORB）

1. 常规参与者：owner + `system-analyst` + `architect` + `bpm`。
2. 高风险议题追加 `admin/hr`。
3. ORB 输出：`owner_review_minutes_ref` + `proposal_priority_matrix_ref`。

#### C) `review -> active` 准入附加条件（相对现状新增）

除既有门禁外，新增：

1. 至少两个连续观测窗口满足目标阈值。
2. 至少一次回滚演练通过且证据可追溯。
3. owner 复盘结论无 `P0/P1` 未关闭项。

### 9.9 Fail-Closed 矩阵（关键场景）

1. 无 owner：阻断提案创建与执行下发。
2. 指标不可比：阻断提案评审，回退补数。
3. 无回滚计划：高风险提案不得进入 M3。
4. M1 非 pass：不得进入 M4 迁移。
5. 迁移证据缺失：`lifecycle-review` 直接失败。
6. active 准入观测窗口不足：禁止 `review -> active`。

### 9.10 证据与落盘规范（新增）

统一落盘至：

1. `runtime_data/evolution/operation-profiles/`
2. `runtime_data/evolution/health-snapshots/`
3. `runtime_data/evolution/issues/`
4. `runtime_data/evolution/proposals/`
5. `runtime_data/evolution/executions/`
6. `runtime_data/evolution/reviews/`

约束：

1. 运行证据默认不写入文档证据目录（公开目录仅保留脱敏样例）。
2. 私有数据遵守 `runtime_data/private-assets/` 隔离策略。

### 9.11 测试与准入口径（新增）

新增 `M5` 专项测试套件目标：

1. `TC-M5-001` 周期触发 happy path。
2. `TC-M5-002` 事件触发 happy path。
3. `TC-M5-003` 无回滚计划 -> Fail-Closed。
4. `TC-M5-004` 指标不可比 -> Fail-Closed。
5. `TC-M5-005` owner 未签收 -> Fail-Closed。
6. `TC-M5-006` `M5 -> M3 -> M1 -> M4` 主链路通过。
7. `TC-M5-007` 主链路验证失败后可回滚且记录闭环。

测试报告必须输出自然语言结论：

1. 测试目标与覆盖边界。
2. 主链路是否可运行。
3. 异常链路是否可恢复/可回退。
4. 是否满足准入。

### 9.12 分阶段落地策略（详细）

#### Phase A（最小闭环）

目标：

1. 不新增专职演化 agent 的前提下跑通 owner 闭环。
2. 形成 `EvolutionProposal` 与执行记录落盘。

交付：

1. `AssetOperationProfile` / `EvolutionProposal` schema（文档与样例）。
2. `evolution-loop-orchestration` 最小流程资产。
3. `tests/m5-self-evolution/` 最小回归入口。

#### Phase B（专职化建设）

目标：

1. 注册 `monitor/analyst/planner`。
2. 注册演化技能族与流程族。

交付：

1. `docs/design/agents/app/evolution/*` 从设计态推进到可注册态。
2. `skill_registry/process_registry/agent_directory` 与 inventory 联动更新。
3. 生命周期保持 `draft/review`，暂不推进 active。

#### Phase C（准入收口）

目标：

1. 建立 `review -> active` 观测窗口与回滚演练硬门禁。
2. 完成 M5 端到端 admission-grade 回归。

DoD：

1. owner 责任契约对全部目标资产可追溯。
2. M5 主链路与异常链路均可复现。
3. 准入结论可审计且无旁路。
