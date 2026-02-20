# ANC v2 产品简报（Product Brief）

最后更新：2026-02-20  
版本：0.1.0-draft  
状态：Draft（BMM）

> 本文档用于对齐“做什么、为谁做、如何衡量是否成功”。  
> 架构冲突裁决以 `/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md` 为准。

## 1. 一句话定义

ANC v2 是一个以流程为业务价值实现基础的通用 AI 原生公司框架（Process-First Company OS），用于将组织能力沉淀为可执行、可治理、可进化的流程资产。

## 2. 背景与问题

当前组织在 AI 能力建设中常见问题：

1. 能力资产化不足：技能、流程、角色定义分散，难以复用。
2. 治理闭环缺失：流程执行有结果但缺证据链，难审计、难回放、难回滚。
3. 迭代机制脆弱：变更常靠经验驱动，缺少 Objective 到 Release 的稳定闭环。
4. 叙事偏移风险：容易把“测试工具能力”误当成“产品核心价值”。

ANC v2 要解决的是“公司级 AI 运行系统”问题，而不是单点测试或单点自动化问题。

## 3. 目标用户与核心场景

### 3.1 目标用户

1. 组织治理者（Founder/CTO/平台负责人）：关心可控性、可审计性、迭代效率。
2. 流程负责人（Architect/BPM Owner）：关心流程定义质量、执行稳定性、发布可回滚。
3. 执行角色（Agent Operator/开发者）：关心输入输出契约清晰、协作成本低、失败可恢复。

### 3.2 关键场景

1. 新能力孵化：从 Objective 出发，快速形成可运行的流程资产包。
2. 存量能力治理：已有流程版本升级时，能稳定判断是否可发布。
3. 失败恢复与复盘：出现失败后可快速定位责任阶段并回滚。
4. 进化迭代：基于运行证据触发改进提案并验证收益。

## 4. 价值主张

### 4.1 对业务

1. 缩短目标到交付路径（Objective Lead Time 下降）。
2. 提升流程一次通过率与稳定性（First Pass Yield 上升）。
3. 降低变更失败成本（Change Failure Rate 下降，MTTR 下降）。

### 4.2 对组织

1. 让知识从“人脑经验”迁移到“流程资产包”。
2. 让协作从“会话记忆驱动”迁移到“证据与文档驱动”。
3. 让演进从“拍脑袋改动”迁移到“门禁+证据+回滚”机制。

### 4.3 对平台

1. 统一运行入口（OpenClaw）与资产治理入口（registry）。
2. 形成可持续迭代的反身自开发框架。
3. 为后续行业化方案提供底座而非临时脚手架。

## 5. 产品范围（Phase 1/2）

### 5.1 In Scope（当前阶段）

1. Process Runtime：支持 1 条端到端元流程可执行。
2. Governance Gate：Verify 门禁强制执行并 Fail-Closed。
3. Evidence Ledger：关键证据链落盘并可追溯。
4. Process Asset Packaging：Agent/Skill/Process 作为可治理内部产品。
5. Evolution Intake（最小）：可记录并管理改进提案入口。

### 5.2 Out of Scope（当前不做）

1. 大规模业务 Agent 建设与行业流程全覆盖。
2. 复杂自动调度优化与高并发性能优化。
3. 跨系统深度集成与细粒度权限工程化。

## 6. 方案概览（高层）

三环产品结构：

1. 运行内核环：BPM + 生命周期治理 + 证据链 + OpenClaw 咬合。
2. 进化引擎环：Objective -> Spec -> Test -> Development 闭环 + 改进提案流。
3. 业务交付环：将流程资产组合成可交付能力与 SLA。

关键约束：

1. 测试属于治理门禁能力，不是产品叙事中心。
2. 未满足证据要求时默认 Fail-Closed。
3. 关键结论必须落盘，不能依赖会话记忆。

## 7. MVP 需求（Product Requirements）

### 7.1 PRD-001 流程执行最小闭环

1. 能创建流程实例并按 Phase 执行。
2. 能记录状态流转（Created/Running/Waiting/Completed/Failed/...）。
3. 能支持失败回退和重试升级链。

### 7.2 PRD-002 门禁与裁决

1. Verify 仅消费标准化 verdict。
2. Scenario 原始结果不可直接作为发布门禁输入。
3. 关键证据缺失时必须拒绝流转。

### 7.3 PRD-003 证据账本

1. 每个 Phase 必须有 input/output/log/decision 的路径锚点。
2. Verify 阶段必须有 transcript/raw_result/normalized_verdict/guard_log。
3. 证据应可用于审计与复盘。

### 7.4 PRD-004 资产治理

1. Agent/Skill/Process 必须有可发现 registry 记录。
2. Active 资产变更必须具备版本与变更记录。
3. Process 定义与 SKILL frontmatter 信息要一致。

## 8. 成功指标（North Star + Guardrail）

### 8.1 North Star

1. Objective Lead Time（目标达成周期）。
2. Process First Pass Yield（流程一次通过率）。
3. Process Reuse Rate（流程资产复用率）。

### 8.2 Guardrail

1. Change Failure Rate（变更失败率）。
2. MTTR for Process Change（流程变更恢复时长）。
3. Human Intervention Ratio（人工介入率）。
4. Evidence Completeness（证据完备率）。

## 9. 里程碑与验收口径

### 9.1 M1（Phase 1）

验收标准：

1. 至少 1 条元流程可运行到 Verify 并给出标准化 verdict。
2. 门禁拒绝逻辑可触发且可追溯原因。
3. 证据链可回放，不依赖外部可视化平台。

### 9.2 M2（Phase 2）

验收标准：

1. 系统基于自身流程上线 1 个新 Skill。
2. 该 Skill 具备完整 Objective/Spec/Test/Development/Evidence 链。
3. 至少形成 1 次运行反馈驱动改进并验证收益。

## 10. 风险与缓解

1. 风险：流程复杂度快速上升。  
   缓解：坚持原子流程优先，分层扩展，限制递归深度。
2. 风险：测试能力喧宾夺主。  
   缓解：指标与文档主线统一为“流程价值交付”。
3. 风险：文档与实现漂移。  
   缓解：执行 SSOT 先行与施工平面强制回写。
4. 风险：自修改引发治理失控。  
   缓解：元层改动必须通过门禁链路并保留回滚快照。

## 11. 依赖与假设

1. OpenClaw 作为统一运行时入口可持续可用。
2. registry 三表持续维护且字段一致。
3. BPM 具备最小实例管理、超时升级、证据记录能力。
4. 组织接受 Phase 1 先治理后扩张的推进节奏。

## 12. 相关文档

1. `/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/architecture/product_requirements.md`
4. `/Users/albus/MyProjects/ANC_v2/docs/architecture/product_design_blueprint.md`
5. `/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md`
6. `/Users/albus/MyProjects/ANC_v2/docs/architecture/construction_plane.md`
