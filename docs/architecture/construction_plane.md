# ANC v2 施工平面（Construction Plane）

最后更新：2026-02-20

> 本文档是 ANC v2 的活施工板，记录当前进展、下一步计划、边界和风险。

## 当前阶段

`Phase 1 - 最小能力建设（架构细化冲刺）`

目标：完成全层文档补完与递归流程骨架，达到“可模块化开工”的决策完备状态。

## 已完成（Done）

- [x] 生命周期统一为 5 态（draft/review/active/deprecated/retired）并同步 3 个 registry contract
- [x] 新增标准体系文档（Agent/Skill/Process/P1-P6）
- [x] 新增递归流程架构文档与 P1-P6 分层文档
- [x] 新增 17 个 P6 原子流程文档
- [x] 新增双主线业务流程文档（内部孵化 + 外部交付 + 复用映射）
- [x] 新增 role handoff 协议与 role responsibility schema
- [x] App 层 Agent 从占位升级为独立角色文档（evolution + delivery）
- [x] 更新 design 索引、layers/modules/skills/processes/inventories 核心文档
- [x] `development-process` canonical 路径固定为 `/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/`

## 进行中（In Progress）

- [ ] 将新增 App Agent、流程与技能逐步纳入 runtime registry（按生命周期进入 review）
- [ ] 执行一致性检查脚本（术语、状态、路径、schema 字段）

## 下一步（Next）

1. 为 P6 原子流程补充 process.json 样板定义。
2. 将 lifecycle-review、registry-sync、escalation 具象化为可执行流程资产。
3. 触发一次双主线 dry-run（文档级）并沉淀证据目录。

## 里程碑

| 编号 | 里程碑 | 判定标准 | 状态 |
|---|---|---|---|
| M0 | 骨架就绪 | SSOT + 模板 + registry 基线 | 已完成 |
| M0.5 | 施工基线 | 角色目录 + P0 meta-skill + development-process + dry-run | 已完成 |
| M1 | 第一次 LLM 评估 | llm-judge 输出结构化 verdict | 进行中 |
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

## 更新纪律

1. 每次会话至少落一个可持久工件。
2. 每次阶段切换必须更新 Done/In Progress/Next。
3. 未落盘结论不作为治理依据。
