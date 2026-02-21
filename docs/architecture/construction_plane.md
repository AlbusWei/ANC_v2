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
- [x] 新增 25 个 P6 原子流程文档（含 AP-018~AP-025）
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

## 进行中（In Progress）

- [ ] 将新增 App Agent、流程与技能逐步纳入 runtime registry（按生命周期进入 review）
- [ ] 执行一致性检查脚本（术语、状态、路径、schema 字段）
- [ ] 将 trigger governance 最小 dry-run 从文档级证据升级到运行级证据
- [ ] 完成 M1 OpenJudge 适配规范与 AP-005/018/019/020/021~025 一致性落盘

## 下一步（Next）

1. 为 P6 原子流程补充 process.json 样板定义。
2. 将 lifecycle-review、registry-sync、escalation 具象化为可执行流程资产。
3. 完成 `review-processes-business` 未闭环项：`governance_bundle` 落地、legacy 语义收敛、canonical 路径策略定稿。
4. 触发一次双主线 dry-run（文档级）并沉淀证据目录。
5. 执行一次 governed-config-change 文档级 dry-run，补齐标准证据包模板。
6. 将 quality gate 相关技能资产从设计落盘推进到 `registry draft`（含 `SKILL.md/TEST.md`）。

## 里程碑

| 编号 | 里程碑 | 判定标准 | 状态 |
|---|---|---|---|
| M0 | 骨架就绪 | SSOT + 模板 + registry 基线 | 已完成 |
| M0.5 | 施工基线 | 角色目录 + P0 meta-skill + development-process + dry-run | 已完成 |
| M1 | 统一测试门禁可用 | 门禁生效 + M3/M4/M5 复用接入 + 证据审计可追溯 | 进行中 |
| M1.5 | 架构细化完成 | L0-L5 + P1-P6 + 双主线 + 原子流程文档齐套 | 已完成 |
| M2 | 第一次 TDD 闭环 | 一个 Skill 从 Test 先行到复测通过 | 待开始 |
| M3 | 第一次流程编排 | BPM 成功调度 3+ Phase 流程 | 待开始 |
| M4 | 第一次自开发 | 系统用自身流程开发并上线新 Skill | 待开始 |

## 开放问题

| 编号 | 问题 | 计划处理阶段 | Owner |
|---|---|---|---|
| Q-001 | OpenClaw session 是否足够支撑严格实例隔离？ | Phase 1 | Albus |
| Q-002 | LLM Judge 多轮评估并发策略如何控成本？ | Phase 1 | Albus |
| Q-003 | 元层自修改审批阈值如何量化？ | Phase 4 | TBD |
| Q-004 | development-process 双路径归一化策略 | Phase 1 | Closed（已归一为 meta canonical） |
| Q-005 | HOLD 专项治理流程如何沉淀为系统流程资产并接管 QA 临时 triage 职责？ | Phase 1 | Closed（已落盘 hold-governance + AP-021~025） |

## 更新纪律

1. 每次会话至少落一个可持久工件。
2. 每次阶段切换必须更新 Done/In Progress/Next。
3. 未落盘结论不作为治理依据。
