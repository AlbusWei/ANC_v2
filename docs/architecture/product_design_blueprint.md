# ANC v2 产品设计总纲（Product Design Blueprint）

最后更新：2026-02-20  
版本：0.1.0-draft

> 本文档用于细化 ANC v2 的产品设计表达与执行蓝图。  
> 架构冲突裁决以 `/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md` 为准。

## 1. 产品定位

ANC v2 的产品定位是：

`以流程为业务价值实现基础的通用 AI 原生公司框架（Process-First Company OS）`

定位含义：

1. ANC v2 不是单一业务应用，而是“构建、运行、治理、进化业务流程资产”的公司级框架。
2. 对外可交付对象优先是“流程能力包”，而非孤立功能。
3. 测试能力是治理子系统，用于门禁与裁决，不是产品叙事中心。

## 2. 目标与非目标

### 2.1 核心目标

1. 将组织经验沉淀为可执行、可复用、可治理的流程资产。
2. 让流程资产具备版本化、证据化、可回放与可回滚能力。
3. 让系统在受控治理下持续完成“运行 -> 反思 -> 改进 -> 再运行”。

### 2.2 非目标

1. 不在 Phase 1 追求大规模业务功能覆盖。
2. 不以“测试框架能力丰富度”作为主产品价值衡量。
3. 不在骨架期引入复杂自动触发和高并发优化。

## 3. 价值模型（Business Model, Product Lens）

### 3.1 核心价值单元

ANC v2 的最小可交易价值单元定义为：

`Process Asset Package = Objective + Process + Policy + Evidence + Release Metadata`

价值解释：

1. Objective 保证“为什么做、做到什么程度”。
2. Process 保证“如何稳定复现”。
3. Policy 保证“何时可发布、何时必须回滚”。
4. Evidence 保证“可审计、可复盘、可追责”。
5. Release Metadata 保证“可版本化治理与升级”。

### 3.2 三层产品形态

1. 框架层（Framework Layer）：运行时、编排、治理、证据链基础设施。
2. 资产层（Asset Layer）：可复用 Skill/Process 模板与能力包。
3. 方案层（Solution Layer）：行业或场景化流程编排方案。

## 4. 产品架构（三环）

### 4.1 运行内核环（Runtime & Governance Core）

职责：

1. 流程编排（BPM）。
2. 生命周期治理（registry + status + version）。
3. 证据链与 Fail-Closed 门禁。
4. OpenClaw 运行时咬合与配置一致性保障。

对应分层：L0-L2。

### 4.2 进化引擎环（Self-Development & Evolution Engine）

职责：

1. Objective -> Spec -> Test -> Development 的可执行闭环。
2. 基于运行反馈触发改进提案与变更执行。
3. 元层自修改门禁（提案、影响分析、沙箱、审批、灰度、回滚）。

对应分层：L3-L4。

### 4.3 业务交付环（Business Delivery Surface）

职责：

1. 将流程资产组合成可交付业务能力。
2. 面向具体场景输出稳定、可审计的结果与 SLA。
3. 支持多业务线复用同一治理骨架，避免重复造轮子。

对应分层：L5。

## 5. 产品对象模型（Product Object Model）

一等对象（产品视角）：

1. `Objective`：业务目标与约束。
2. `Process Asset`：可执行流程定义（原子/复合）。
3. `Capability Package`：Agent + Skill + Process 的发布组合。
4. `Policy`：门禁、审批、升级、回滚规则。
5. `Evidence Ledger`：输入输出、日志、verdict、guard_log 的证据账本。
6. `Evolution Proposal`：基于运行证据生成的改进提案。

对象间主关系：

`Objective -> Process Asset -> Capability Package -> Delivery Result -> Evidence -> Evolution Proposal -> Objective`

## 6. 核心流程产品化（从“能跑”到“可运营”）

### 6.1 价值交付主链

`Intake -> Objective Clarify -> Spec -> Test Design -> Development -> Verify -> Release -> Operate`

要求：

1. 每个阶段输出必须落盘并可被下游引用。
2. Verify 的判定输入必须为归一化 verdict，不得直连底层原始结果。
3. Release 必须绑定版本与回滚策略。

### 6.2 进化主链

`Observe -> Diagnose -> Prioritize -> Propose -> Validate -> Rollout -> Measure`

要求：

1. 进化提案必须包含收益假设与风险假设。
2. 高风险改动必须进入人类审批断路器。
3. 回滚预案缺失时禁止发布。

## 7. 指标体系（避免测试中心化）

北极星指标：

1. Objective Lead Time（目标达成周期）。
2. Process First Pass Yield（流程一次通过率）。
3. Change Failure Rate（变更失败率）。
4. MTTR for Process Change（流程变更恢复时长）。
5. Human Intervention Ratio（人工介入率）。
6. Process Reuse Rate（流程资产复用率）。
7. Evidence Completeness（证据完备率）。

说明：测试通过率是治理观测指标之一，不是北极星指标。

## 8. Phase 1/2 产品化里程碑细化

### 8.1 Phase 1（最小可运行闭环）

可验收交付：

1. Process Runtime：可执行 1 条端到端元流程（含 p4 门禁）。
2. Evidence Ledger：可回放完整证据链（transcript/raw_result/normalized_verdict/guard_log）。
3. Governance Gate：Fail-Closed 生效并可追溯拒绝原因。
4. Product Narrative Alignment：文档与流程表达均以“流程价值”而非“测试能力”为主线。

### 8.2 Phase 2（自开发闭环跑通）

可验收交付：

1. 系统使用自身 `development-process` 开发并上线至少 1 个新 Skill。
2. 新 Skill 发布附带完整 Objective/Spec/Test/Evidence 证据链。
3. 形成至少 1 次“运行反馈驱动改进”闭环记录。

## 9. 与现有 SSOT 的对齐

本文件与现有 SSOT 对齐关系：

1. 架构主约束：`/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md`
2. 流程原语与执行协议：`/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`
3. 测试治理规范：`/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md`
4. 上下文与证据传递：`/Users/albus/MyProjects/ANC_v2/docs/architecture/context_protocol.md`
5. 阶段施工状态：`/Users/albus/MyProjects/ANC_v2/docs/architecture/construction_plane.md`

## 10. 下一步落地建议

1. 将北极星指标映射到 Phase 1 的每次流程执行报告模板。
2. 为 `development-process` 增加“价值交付视角”输出字段（目标达成影响、复用价值、风险暴露）。
3. 在 registry 增加可选元字段：`value_domain`、`business_outcome_ref`、`evolution_priority`。
