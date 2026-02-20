# ANC v2 施工平面（Construction Plane）

最后更新：2026-02-20

> 本文档是 ANC v2 的活施工板，记录当前进展、下一步计划、边界和风险。
> 任何实质推进后应同步更新本文件。

## 当前阶段

`Phase 1 - 最小能力建设`

目标：基于已完成的 0.5 骨架，跑通最小可执行能力链（角色 + P0 meta-skill + development-process）。

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
- [x] Kernel/Control 最小角色目录落盘（admin/architect/hr/kernel-dev/qa/bpm）
- [x] P0 meta-skill 草案落盘（llm-judge/spec-writer/test-designer）
- [x] `development-process` 元流程实例化（SKILL.md + process.json + PROCESS.md）
- [x] Phase 0.5 dry-run 证据链落盘（含 context/state/evidence/artifacts）
- [x] OpenClaw Phase 0.5 配置片段落盘（`agents.list` + `skills.entries`）
- [x] 新增 `scenario-runner` 元技能与测试资产（`SKILL.md` + `tests/scenario-runner/TEST.md`）
- [x] `llm-judge` 升级到 v0.2 契约并补齐 Scenario 归一化规则与 schema
- [x] `processes/meta/development-process/process.json` 升级到 v0.2（Scenario Verify 门禁版）
- [x] `processes/development-process` 标注为 Phase 0.5 示例归档，运行 SSOT 固定为 `processes/meta/*`
- [x] registry 与 openclaw 片段同步：`scenario-runner`、`llm-judge@0.2.0`、`development-process@0.2.0`
- [x] 产品叙事纠偏落盘：新增 `/Users/albus/MyProjects/ANC_v2/docs/architecture/product_design_blueprint.md`，明确 ANC v2 为 Process-First Company OS，测试定位回归治理门禁

## Phase 0.5 完成判定

1. 角色基线：`admin/architect/hr/kernel-dev/qa/bpm` 均有目录与最小五件套。`完成`
2. P0 meta-skill：`llm-judge/spec-writer/test-designer` 均有 `SKILL.md + TEST.md`。`完成`
3. 元流程：`development-process` 具备 `SKILL.md + process.json + PROCESS.md`。`完成`
4. 证据链：存在可回放 dry-run 实例目录。`完成`
5. OpenClaw 咬合：存在 `agents.list + skills.entries` 配置片段。`完成`
- [x] 模板职责澄清：`TEST.md` 迁移到 `/Users/albus/MyProjects/ANC_v2/tests/template/`，并将说明文档上移到 `skills/`、`processes/`、`tests/` 根目录
- [x] 首个真实示例资产落盘：`skills/skill-creator`、`processes/development-process` 与对应 `tests/`、registry 条目

## 进行中（In Progress）

- [ ] 将 `development-process(p4)` 接入 Scenario 执行 + 归一化门禁链
- [ ] 为 `development-process` 增加一轮失败回环样例证据（p4 fail -> p3 retry）

说明：以上两项需要一次真实流程执行与证据回放验证，完成前不应标记为“门禁已上线”。

## 下一步（Next）

`Phase 1 - 最小可运行闭环`

1. 在 OpenClaw 本地配置中启用 ANC_v2 的 `skills.entries`（含 `scenario-runner`）与 `agents.list`。
2. 触发一次真实流程执行（非 dry-run），验证 `p4` 输出 `normalized_verdict.json`。
3. 形成 Scenario objective 评估证据链（`transcript/raw_result/guard_log`）并接入测试报告模板。
4. 将北极星指标（Objective Lead Time / First Pass Yield / Reuse Rate）接入 Phase 1 周报模板。

## 后续（Later）

1. Phase 1.2：启用 subjective A/B 多轮评估（默认 N=9）并接入统计裁决。
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
| M0 | 骨架就绪 | SSOT + 支撑文档 + 模板/registry 基线到位 | 已完成 |
| M0.5 | 施工基线 | 角色目录 + P0 meta-skill + development-process + dry-run | 已完成 |
| M1 | 第一次 LLM 评估 | `llm-judge` 可输出 pass/fail + remarks + suggestions | 进行中 |
| M1.1 | Scenario Objective 门禁 | `p4` 可输出标准化 verdict + fail-closed guard + 证据链 | 进行中 |
| M1.2 | Scenario Subjective A/B | 9 轮盲测可输出胜率裁决与 human-review 分流 | 待开始 |
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
| Q-002 | LLM Judge 多轮评估并发策略如何控成本？ | Phase 1.2 | Albus |
| Q-003 | 元层自修改审批阈值如何量化？ | Phase 4 | TBD |
| Q-004 | 现有 `processes/development-process` 与 `processes/meta/development-process` 的归一化策略 | Phase 1 | architect |

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
