# ANC v2 施工平面（Construction Plane）

最后更新：2026-02-21

> 本文档是 ANC v2 的活施工板，记录当前进展、下一步计划、边界和风险。

## 当前阶段

`Phase 1 - 最小能力建设（架构细化冲刺）`

目标：完成全层文档补完与递归流程骨架，达到“可模块化开工”的决策完备状态。

## 已完成（Done）

- [x] 生命周期统一为 5 态（draft/review/active/deprecated/retired）并同步 3 个 registry contract
- [x] 新增标准体系文档（Agent/Skill/Process/P1-P6）
- [x] 新增递归流程架构文档与 P1-P6 分层文档
- [x] 新增 31 个 P6 原子流程文档（含 AP-018~AP-031）
- [x] 新增双主线业务流程文档（内部孵化 + 外部交付 + 复用映射）
- [x] 新增 role handoff 协议与 role responsibility schema
- [x] App 层 Agent 从占位升级为独立角色文档（evolution + delivery）
- [x] 更新 design 索引、layers/modules/skills/processes/inventories 核心文档
- [x] `development-process` canonical 路径固定为 `/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/`
- [x] 完成 Entire 项目接入基线（`.entire/settings.json` + git hooks）并落盘 Codex 桥接协议/技能（`entire-codex-sync`）
- [x] 在 `/Users/albus/MyProjects/ANC_v2/AGENTS.md` 增加 Codex 强制 Entire 管理流程（start/sync/commit-check/end + Fail-Closed）
- [x] 明确 OpenClaw 配置治理分工（App -> BPM -> Admin），并新增 personal-assistant 入口角色设计与 registry 记录
- [x] 新增 `governed-config-change` 可执行流程资产（`processes/meta/governed-config-change/`）并注册到 `process_registry`
- [x] 落盘 Skill 双层契约设计（Registry Contract + Capability Contract）并新增 ADR-11/ADR-12
- [x] 将 Capability Contract 固定为 `SKILL.md` 机器块（固定标题 + YAML），并纳入 `registry_contract_tool.py verify` 全量校验
- [x] 将模块依赖矩阵升级为类型化依赖并明确 `M3/M4` 并行建设与汇合门（`M1` 统一门禁复用）
- [x] 收敛 canonical process manifest 到标准字段（`process_level/control_flow/fail_policy/lineage_policy`）
- [x] 新增 layer/module 联动文档门禁：新增或变更 skill/process/agent 必须同回合补齐设计文档 + inventory + registry + 施工平面
- [x] 完成 M1 质量门禁二次重构：`quality-gate-preparation` + `quality-gate-evaluation` + `hold-governance` 连续性闭合
- [x] 完成 M2 触发运行时骨架落盘：`trigger-schedule-runtime` + `trigger-event-runtime` + AP-026~AP-031 + 6 个 `sys.bpm.*` 核心技能
- [x] 完成 M3 自开发骨架落盘：`full-development/hotfix/refactor` 流程资产 + `objective-writer/agent-creator/process-creator/template-validator/skill-creator` 技能注册
- [x] 完成 M6 施工治理资产落盘：`construction-plane-governance` 流程 + `sys.arch.construction-audit` 技能 + M6 详细设计重构
- [x] 建立 M6 × OpenSpec Hybrid 协同协议并明确 Architect 语义 owner 机制
- [x] 完成 OpenSpec 协同完整 schema 与包装技能落盘：`openspec-collaboration-schema` + `system.integration.openspec-sync`
- [x] 锁定回合追溯主键：`1 round = 1 OpenSpec change = N Entire checkpoints = N commits`
- [x] 锁定证据写入策略：提交级证据进入 `round-evidence.jsonl`，施工平面主文档仅在回合关闭时汇总
- [x] 锁定 `round_id` 规范：`R-YYYYMMDD-M6-<change_key>-NN`，`NN` 按同一 `change_key` 递增
- [x] 完成 M6 AP 化补齐：新增 AP-032~AP-036 并将 `construction-plane-governance` 全 phase 映射到专用 AP

## 进行中（In Progress）

- [ ] 将新增 App Agent、流程与技能逐步纳入 runtime registry（按生命周期进入 review）
- [ ] 执行一致性检查脚本（术语、状态、路径、schema 字段）
- [ ] 将 trigger governance 最小 dry-run 从文档级证据升级到运行级证据
- [ ] 完成 M1 OpenJudge 适配规范与 AP-005/018/019/020/021~025 一致性落盘
- [ ] 完成 trigger runtime 动态策略实证校准并形成参数回写节奏
- [ ] 建立 `runtime-policy-calibration` 治理节奏并纳入 M1/M2 首批后验议题
- [ ] 触发 M3 `full-development/hotfix/refactor` 首轮运行级 dry-run 并沉淀证据
- [ ] 按“文档级先行”策略完成 M6 × OpenSpec 双向映射样板与冲突裁决模板
- [ ] 触发 `construction-plane-governance` 首轮运行级 dry-run 并沉淀证据（后置）

## 下一步（Next）

1. 为 P6 原子流程补充 process.json 样板定义。
2. 将 lifecycle-review、registry-sync、escalation 具象化为可执行流程资产。
3. 完成 `review-processes-business` 未闭环项：`governance_bundle` 落地、legacy 语义收敛、canonical 路径策略定稿。
4. 触发一次双主线 dry-run（运行级）并沉淀证据目录。
5. 执行一次 governed-config-change 运行级 dry-run，补齐标准证据包模板。
6. 将 quality gate 相关技能资产从设计落盘推进到 `registry draft`（含 `SKILL.md/TEST.md`）。
7. 进行 trigger runtime 动态策略回放并回写 `catchup_policy_ref` 校准证据。
8. 将 M1 测试时长估计与 M2 动态策略问题统一纳入 `runtime-policy-calibration` 治理回路。
9. 收敛 M6 周期审查节奏与 owner 责任模型，并写入治理流程基线。
10. 与 OpenSpec 协同线程联调一次“冲突裁决 -> 双向回写”演练。
11. 为 `round-evidence.jsonl` 补充校验脚本（事件顺序、checkpoint/commit 对账、`round_id` 正则校验）。

## 里程碑

| 编号 | 里程碑 | 判定标准 | 状态 |
|---|---|---|---|
| M0 | 骨架就绪 | SSOT + 模板 + registry 基线 | 已完成 |
| M0.5 | 施工基线 | 角色目录 + P0 meta-skill + development-process + dry-run | 已完成 |
| M1 | 统一测试门禁可用 | 门禁生效 + M3/M4/M5 复用接入 + 证据审计可追溯 | 进行中 |
| M1.5 | 架构细化完成 | L0-L5 + P1-P6 + 双主线 + 原子流程文档齐套 | 已完成 |
| M2 | 第一次 TDD 闭环 | 一个 Skill 从 Test 先行到复测通过 | 进行中（BPM runtime 骨架已落盘） |
| M3 | 第一次流程编排 | BPM 成功调度 3+ Phase 流程 | 进行中（M3 资产已落盘，待运行级 dry-run） |
| M4 | 第一次自开发 | 系统用自身流程开发并上线新 Skill | 待开始 |

## 开放问题

| 编号 | 问题 | 计划处理阶段 | Owner |
|---|---|---|---|
| Q-001 | OpenClaw session 是否足够支撑严格实例隔离？ | Phase 1 | Albus |
| Q-002 | LLM Judge 多轮评估并发策略如何控成本？ | Phase 1 | Albus |
| Q-003 | 元层自修改审批阈值如何量化？ | Phase 4 | TBD |
| Q-004 | development-process 双路径归一化策略 | Phase 1 | Closed（已归一为 meta canonical） |
| Q-005 | HOLD 专项治理流程如何沉淀为系统流程资产并接管 QA 临时 triage 职责？ | Phase 1 | Closed（已落盘 hold-governance + AP-021~025） |
| Q-006 | `sys.bpm.process-parser/process-scheduler/lineage-guard` 应拆分为独立技能还是并入 `process-instance-manager`？ | Phase 1 | Closed（已决策并入 `process-instance-manager` 子能力） |
| Q-007 | `trigger-schedule-runtime` 与 `trigger-event-runtime` 是否继续拆分出统一父流程（如 `trigger-runtime-supervisor`）？ | Phase 1 | Closed（结论：当前保持双 P4 流程；如需收口，引入 P5 `trigger-runtime-supervisor` 模式） |
| Q-008 | 动态 `catchup_policy_ref` 的校准周期与最小样本量如何设定，才能兼顾稳定性与响应速度？ | Phase 1 | system-analyst -> architect/admin/bpm |
| Q-009 | `construction-plane-governance` 在 Phase 1 先文档级演练还是直接运行级 dry-run？ | Phase 1 | Closed（文档级先行，运行级后置） |
| Q-010 | `sys.arch.construction-audit` 长期 owner 固定 architect 还是 architect+bpm 双 owner？ | Phase 1 | Closed（architect 为语义 owner，bpm 负责编排执行） |
| Q-011 | M6 审查节奏采用“变更触发”还是“周节奏+变更触发”双轨？ | Phase 1 | Closed（变更触发 + system-analyst 可调频巡检） |
| Q-012 | OpenSpec 双向映射的最小字段是否固化为强制 schema（如 `openspec_ref/decision_snapshot_ref/sync_status`）？ | Phase 1 | Closed（已升级为完整强制 schema） |
| Q-013 | OpenSpec 巡检触发阈值如何分级（变更密度、风险等级、未决项数量）？ | Phase 1 | system-analyst -> architect |
| Q-014 | OpenSpec 与施工回合绑定粒度是否固定为 `1 round = 1 change`？ | Phase 1 | Closed（固定为 `1 round = 1 change`） |
| Q-015 | 提交证据应实时写施工平面主文档还是独立日志？ | Phase 1 | Closed（提交级进入 JSONL，主文档仅关回合汇总） |

## 更新纪律

1. 每次会话至少落一个可持久工件。
2. 每次阶段切换必须更新 Done/In Progress/Next。
3. 未落盘结论不作为治理依据。
