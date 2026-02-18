# ANC v2 施工平面（Construction Plane）

最后更新：2026-02-18

> 本文档是 ANC v2 的活施工板，记录当前进展、下一步计划、边界和风险。
> 任何实质推进后应同步更新本文件。

## 当前阶段

`Phase 0 - 手动自举`

目标：完成架构塑形，建立统一施工平面与最小治理骨架。

## 已完成（Done）

- [x] 架构 SSOT 初稿：`/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md`
- [x] 流程 SSOT 初稿：`/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`
- [x] 施工平面初稿：本文件
- [x] 反思补强：元层/对象层、六层架构、模块依赖、门禁链路
- [x] 新增测试/上下文/术语三份支撑文档
- [x] 模板基线：Agent/Skill/Process/Test 模板落盘
- [x] registry 空壳初始化：agent/skill/process 三表
- [x] OpenClaw 接口契约文档（配置/CLI/技能加载）补齐
- [x] Registry 契约文档补齐并回填字段级 contract
- [x] Skill/Process 模板升级为 Agent Skills 规范兼容格式
- [x] 模板职责澄清：`TEST.md` 迁移到 `/Users/albus/MyProjects/ANC_v2/tests/template/`，并将说明文档上移到 `skills/`、`processes/`、`tests/` 根目录
- [x] 首个真实示例资产落盘：`skills/skill-creator`、`processes/development-process` 与对应 `tests/`、registry 条目

## 进行中（In Progress）

- [ ] 定义 Kernel/Control 最小角色集与职责分配
- [ ] 确认第一个端到端流程（development-process 最简版）
- [ ] 根据 OpenClaw 本地配置落地第一版 `skills.entries` 与 `agents.list`

## 下一步（Next）

`Phase 0.5 - 模板与注册表基线`

1. 锁定第一批 P0 meta-skill：`llm-judge`, `spec-writer`, `test-designer`。
2. 定义第一个 meta-process：`development-process` 最简版。
3. 完成一次端到端 dry-run（手动触发，文档全链路留痕）。

## 后续（Later）

1. Phase 1：BPM + P0 meta-skill 跑通最简闭环。
2. Phase 2：首次“系统用自身流程开发新 Skill”。
3. Phase 3：产品化治理（版本、健康度、退役）。
4. Phase 4：自进化闭环接入。
5. Phase 5：元层安全自修改成熟。

## 当前明确不做（Not In Scope）

1. 业务层 Agent 大规模建设。
2. 自动触发机制与复杂调度优化。
3. 多层递归与高并发性能优化。
4. 过重权限细化和跨系统深度集成。

## 里程碑

| 编号 | 里程碑 | 判定标准 | 状态 |
|---|---|---|---|
| M0 | 骨架就绪 | SSOT + 支撑文档 + 模板/registry 基线到位 | 进行中 |
| M1 | 第一次 LLM 评估 | `llm-judge` 可输出 pass/fail + remarks + suggestions | 待开始 |
| M2 | 第一次 TDD 闭环 | 一个 Skill 完成 Test 先行 -> 开发 -> 复测通过 | 待开始 |
| M3 | 第一次流程编排 | BPM 成功调度 3+ Phase 流程 | 待开始 |
| M4 | 第一次自开发 | 系统用 development-process 开发并上线新 Skill | 待开始 |

## ADR（架构决策记录）

| 编号 | 决策 | 原因 | 日期 |
|---|---|---|---|
| ADR-001 | 采用因果驱动链而非并列三驱动 | 消除冲突优先级歧义 | 2026-02-18 |
| ADR-002 | 文档即通信，不依赖会话记忆 | 提高可审计性和恢复能力 | 2026-02-18 |
| ADR-003 | Phase 0 以手动自举为主 | 塑形阶段避免早期自动化失真 | 2026-02-18 |
| ADR-004 | 原子流程作为最小编排单元 | 明确责任人和 I/O 证据 | 2026-02-18 |
| ADR-005 | BPM 使用栈帧式递归隔离 | 防止父子流程上下文污染 | 2026-02-18 |

## 开放问题

| 编号 | 问题 | 计划处理阶段 | Owner |
|---|---|---|---|
| Q-001 | OpenClaw session 是否足够支撑严格实例隔离？ | Phase 1 | Albus |
| Q-002 | LLM Judge 多轮评估并发策略如何控成本？ | Phase 1 | Albus |
| Q-003 | 元层自修改审批阈值如何量化？ | Phase 4 | TBD |

## 风险与应对

1. 风险：文档过泛无法指导实现。  
   应对：每条关键规则都以“可检查字段”表达。
2. 风险：实现先行导致文档漂移。  
   应对：执行“先改 SSOT，再改实现”的硬规则。
3. 风险：过早复杂化流程。  
   应对：先跑最小闭环，再扩展并发/递归。

## 更新纪律

1. 每次会话至少落一个可持久工件。
2. 每次阶段切换必须更新本文件 `Done/In Progress/Next`。
3. 未落盘结论不作为发布与治理依据。
