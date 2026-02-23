# ANC v2 施工平面（Construction Plane）

最后更新：2026-02-23

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
- [x] 完成 M1 第一批技能开发：`sys.qa.*` 七个技能统一迁移到 `skills/system/qa/*`，补齐 Capability Contract、最小可执行脚本、P0 测试与 registry 联动
- [x] 完成模板基座标准化：升级 `skills/template` 与 `skills/skill-creator`，形成本地化标准脚手架与 review/smoke 评审基线
- [x] 完成 M1 QA 技能运行级复核：OpenJudge 真执行链路与 LLM-as-Judge Fail-Closed 在 `runtime-validation-round-2` 落盘（objective/regression pass，subjective hold，llm-missing-key test_invalid）
- [x] 完成 M1 QA 动态评测补强：`evaluation-runner` 增加 listwise 主观盲测与 judge 错误分类（unsupported model -> `test_invalid`），并在 `runtime-validation-round-3` 落盘 strict config 证据
- [x] 完成 LLM-as-Judge 跑通验证：模型切换 `gpt-5.3-codex` 后，objective + subjective(listwise) 均在 `runtime-validation-round-4` 真实通过
- [x] 新增多 worktree 分支协同技能：`system.ops.git-worktree-sync`（`source -> parent -> siblings`，冲突/大规模 WIP 均 Fail-Closed）
- [x] 锁定回合追溯主键：`1 round = 1 OpenSpec change = N Entire checkpoints = N commits`
- [x] 锁定证据写入策略：提交级证据进入 `round-evidence.jsonl`，施工平面主文档仅在回合关闭时汇总
- [x] 锁定 `round_id` 规范：`R-YYYYMMDD-M6-<change_key>-NN`，`NN` 按同一 `change_key` 递增
- [x] 完成 M6 AP 化补齐：新增 AP-032~AP-036 并将 `construction-plane-governance` 全 phase 映射到专用 AP
- [x] 完成 M6 执行闭环脚本：`manual_task_runner` + `construction_audit` + `round_evidence_tool` + `run_round`
- [x] 完成 M6 专项门禁：`registry_contract_tool.py verify-m6`
- [x] 完成 M6 首轮运行级 dry-run（A 通过，B/C Fail-Closed），并落盘证据索引 `docs/design/modules/evidence/construction-plane/README.md`
- [x] 将 `construction-plane-governance`、`sys.arch.construction-audit`、`system.integration.openspec-sync` 生命周期从 `draft` 提升到 `review`
- [x] 完成 `m2-bpm-runtime-hardening` W2 配置治理闭环：`governed-config-change`/`config-change-gatekeeper`/`system-config-updater` 可执行，`TC-GCC-001~003` 运行级通过并落盘证据（`docs/design/modules/evidence/bpm-runtime/w2_*`）
- [x] 完成 `m2-bpm-runtime-hardening` W5（门禁收口与状态提升）：新增 `verify-m2` 专项校验，`verify/verify-m2/verify-m6` 与 post-dev regression 同回合通过，关闭 `Q-001`，并将 `system-analyst`、`sys.arch.system-feedback-digest`、`runtime-policy-calibration` 生命周期统一收敛到 `review`（不推进 `active`）
- [x] 新增 `lifecycle-review` 最小可执行流程资产（owner=`hr`，status=`draft`），并完成 design/inventory/registry/施工平面联动更新（Thread-2）
- [x] 完成 Thread-4 状态联动收口：`qa/bpm/admin/architect/hr` 生命周期统一推进到 `review`；`lifecycle-review` 由 `draft` 推进到 `review`；`system-analyst` 保持“分析输入，不做 lifecycle owner”边界
- [x] 完成 `R-20260222-M6-m1-quality-gate-runtime-closure-01` 回合关闭包：`round-output.json`、`round-evidence.jsonl`、`round_close_summary.md`、`openspec-sync-record.json`、`registry_verify.log`，并通过 `verify` 与 `verify-m6`
- [x] 完成 `m1-quality-gate-runtime-closure` OpenSpec 归档：补齐 `specs/**` deltas 与 Scenario，`openspec validate` 通过并归档至 `openspec/changes/archive/2026-02-22-m1-quality-gate-runtime-closure/`
- [x] 完成 `m3-self-development-e2e-online` Session3 运行资产落地：新增 `impact-analyzer/release-manager` 技能、`registry-sync/escalation` 流程、`release-manager-agent` 目录，并完成 registry/OpenSpec/施工平面联动
- [x] 完成 `m3-self-development-e2e-online` Session4 测试基座：新增 `tests/m3-self-development/{TEST.md,live_cases.md,run_tc_online.py}`，复用 `m3-runtime + m1-runtime` runner 形成四类断言并预留 Session5/6 case 体系
- [x] 完成 `m3-meta-asset-quality-hardening` Phase2 流程资产重构：7 个历史包装流程全部退役，`full-development/hotfix/refactor/development-process` 全量替换为现行 P5 子流程链，并完成 process registry、process inventory、施工平面同步
- [x] 完成 `m3-meta-asset-quality-hardening` Phase3 元技能执行级升级：8 个目标元技能统一推进到 `review`，4 个 creator/validator runner 统一为 `--input/--output/[--report]` 契约，并落地 `meta-skill-creator` 运行名治理（`skill-creator` 仓库内软禁用）
- [x] 完成 `m3-meta-asset-quality-hardening` Phase4 联动闭合：design + inventory + registry + OpenSpec + 施工平面对齐，11 个流程生命周期统一收敛到 `review`，并明确本轮不推进 `active`
- [x] 完成 `m3-meta-asset-quality-hardening` Phase9 `full-development` 首轮运行级真实分发 dry-run：`TC-FULL-DEV-PROC-001` 在 8 phase 下通过，真实 openclaw 分发 + 同 actor 跨 phase 会话隔离校验通过

## 进行中（In Progress）

- [ ] 基于 `m2-bpm-runtime-hardening` 本轮收口结果，补齐从 `review` 推进到 `active` 的观测窗口、回滚演练与准入阈值
- [ ] 将新增 App Agent、流程与技能逐步纳入 runtime registry（按生命周期进入 review）
- [ ] 执行一致性检查脚本（术语、状态、路径、schema 字段）
- [ ] 将 trigger governance 最小 dry-run 从文档级证据升级到运行级证据
- [ ] 完成 trigger runtime 动态策略实证校准并形成参数回写节奏
- [ ] 建立 `runtime-policy-calibration` 治理节奏并纳入 M1/M2 首批后验议题
- [ ] 触发 M3 `hotfix/refactor` 首轮运行级 dry-run 并沉淀证据（`full-development` 已完成）
- [ ] 基于首轮证据推进 M6 第二轮运行级回归（含 git-range + trailer 实盘对账）
- [ ] 推进 `m3-self-development-e2e-online`：完成 Session5~Session7 运行级测试与双主线 E2E 收口（Session4 测试基座已落地）

## 下一步（Next）

1. 为 P6 原子流程补充 process.json 样板定义。
2. 完成 `review-processes-business` 未闭环项：`governance_bundle` 落地、legacy 语义收敛、canonical 路径策略定稿。
3. 基于 `tests/m3-self-development/run_tc_online.py` 执行 Session5 内部主线 E2E 并沉淀证据。
4. 触发一次双主线 dry-run（运行级）并沉淀证据目录。
5. 执行一次 governed-config-change 运行级 dry-run，补齐标准证据包模板。
6. 在后续线程补齐 `lifecycle-review` 与 M3 接线并扩展多场景运行证据。
7. 进行 trigger runtime 动态策略回放并回写 `catchup_policy_ref` 校准证据。
8. 将 M1 测试时长估计与 M2 动态策略问题统一纳入 `runtime-policy-calibration` 治理回路。
9. 收敛 M6 周期审查节奏与 owner 责任模型，并写入治理流程基线。
10. 与 OpenSpec 协同线程联调一次“冲突裁决 -> 双向回写”演练。
11. 收敛 `verify-m2`/`verify-m6` 与 CI/pre-close gate 集成方式，避免人工绕过。

## m3-self-development-e2e-online 会话推进计划（Session2~Session7）

> 前置约束：Session1 仅完成审计与基座，不做功能开发；生命周期目标上限为 `review`（禁止推进 `active`）。

| 会话 | 依赖 | 会话目标 | 输入（必须具备） | 输出（必须落盘） | DoD（命令化门禁） |
|---|---|---|---|---|---|
| Session2 | Session1 | 完成 M3 设计闭合差距收敛（仅设计，不落运行资产） | `openspec/changes/m3-self-development-e2e-online/m3-gap-baseline.md`、`openspec/changes/m3-self-development-e2e-online/design.md`、`openspec/changes/m3-self-development-e2e-online/tasks.md`、`openspec/changes/m3-self-development-e2e-online/specs/**/spec.md` | 设计闭合产物清单：`docs/design/processes/{registry-sync-process.md,escalation-process.md}`、`docs/design/skills/{system-skills.md,self-development-skills.md}`、`docs/design/agents/app/delivery/release-manager-agent.md`、`docs/design/modules/M3-self-development.md`、inventory 联动文档 + 拆分状态后的 `m3-gap-baseline.md` | `openspec validate m3-self-development-e2e-online --json` pass；`python3 shared/registry/registry_contract_tool.py verify` pass；`m3-gap-baseline.md` 明确 `closed(design)` 与 `open(implementation)`；DoD 仅判设计文档闭合，不宣称运行可用 |
| Session3 | Session2 | 落地五项缺失资产最小可执行骨架（已完成 2026-02-23） | Session2 闭合清单 + `docs/design/skills/system-skills.md` + `docs/design/processes/governance-processes.md` + `docs/design/agents/app/delivery/release-manager-agent.md` | `skills/system/{impact-analyzer,release-manager}/`、`processes/meta/{registry-sync,escalation}/`、`agents/app/delivery/release-manager-agent/`、`tests/m3-runtime/run_skill_contract_validation.py`；对应 design/inventory/registry/施工平面联动更新 | `python3 tests/m3-runtime/run_skill_contract_validation.py` pass；`python3 shared/registry/registry_contract_tool.py verify` pass；`openspec validate m3-self-development-e2e-online --json` pass；状态仅到 `draft/review` |
| Session4 | Session3 | 建立 M3 专项运行级测试扩展基座（已完成 2026-02-23） | Session3 资产 + `tests/m3-runtime/run_skill_contract_validation.py` + M3 三流程 manifest | 新增 `tests/m3-self-development/{TEST.md,live_cases.md,run_tc_online.py}`，并在 `docs/design/modules/evidence/self-development/e2e-online/session4-foundation/latest/` 输出四类断言证据与汇总报告 | `python3 tests/m3-self-development/run_tc_online.py --help` pass；默认执行覆盖主链路/异常链路/Fail-Closed/回退返工四类；预留 case 在 Session4 强制执行时 Fail-Closed |
| Session5 | Session4 | 完成内部主线 E2E | Session4 测试基座（`tests/m3-self-development/run_tc_online.py` + `tests/m3-self-development/live_cases.md`）+ M3 canonical 流程资产 | 内部主线 E2E 证据目录与摘要（包含关键异常可回退记录） | 内部主线关键场景通过；失败场景可恢复/可回退；`M3 -> M1 -> M4` 门禁链路有证据且无旁路 |
| Session6 | Session5 | 完成外部主线 E2E（复用 M3 canonical） | Session5 内部主线基线 + 外部交付主线上下文 | 外部主线 E2E 证据目录、内外复用对照结论 | 外部主线关键场景通过；复用路径不绕过 M3 canonical；旁路检测为 0 |
| Session7 | Session6 | 执行全链路对账并收敛到 review | Session1~Session6 全量证据 + OpenSpec/registry/施工平面改动 | 收口记录、对账报告、回合关闭证据 | `openspec validate m3-self-development-e2e-online --json` pass；`python3 shared/registry/registry_contract_tool.py verify` pass；提交后 `git log -1 --pretty=raw` 含 `Entire-Checkpoint`；生命周期仅收敛到 `review` |

## 里程碑

| 编号 | 里程碑 | 判定标准 | 状态 |
|---|---|---|---|
| M0 | 骨架就绪 | SSOT + 模板 + registry 基线 | 已完成 |
| M0.5 | 施工基线 | 角色目录 + P0 meta-skill + development-process + dry-run | 已完成 |
| M1 | 统一测试门禁可用 | 门禁生效 + M3/M4/M5 复用接入 + 证据审计可追溯 | 进行中（`sys.qa.*` 七技能 active pilot 已落盘） |
| M1.5 | 架构细化完成 | L0-L5 + P1-P6 + 双主线 + 原子流程文档齐套 | 已完成 |
| M2 | 第一次 TDD 闭环 | 一个 Skill 从 Test 先行到复测通过 | 进行中（BPM runtime 骨架已落盘） |
| M3 | 第一次流程编排 | BPM 成功调度 3+ Phase 流程 | 进行中（M3 资产已落盘，待运行级 dry-run） |
| M4 | 第一次自开发 | 系统用自身流程开发并上线新 Skill | 待开始 |

## 开放问题

| 编号 | 问题 | 计划处理阶段 | Owner |
|---|---|---|---|
| Q-001 | OpenClaw session 是否足够支撑严格实例隔离？ | Phase 1 | Closed（W5 门禁收口完成：`verify/verify-m2/verify-m6` + post-dev regression） |
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
