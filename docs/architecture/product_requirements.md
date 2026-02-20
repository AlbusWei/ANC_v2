# ANC v2 产品需求文档（PRD）

最后更新：2026-02-20  
版本：0.1.0-draft  
状态：Draft（BMM）

> 本文档定义 ANC v2 在 Phase 1/2 的产品需求、验收标准与发布边界。  
> 冲突裁决顺序：`Objective > Spec > Test > Implementation`。  
> 架构冲突以 `/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md` 为准。

## 1. 文档目标

1. 将 `/Users/albus/MyProjects/ANC_v2/docs/architecture/product_brief.md` 的产品意图转为可执行需求。
2. 形成可追踪的需求编号、验收标准与里程碑。
3. 保障需求与 SSOT、流程契约、测试门禁的一致性。

## 2. 产品范围与边界

### 2.1 In Scope（Phase 1/2）

1. 流程执行最小闭环（Process Runtime）。
2. 验证与门禁（Governance Gate）。
3. 证据账本（Evidence Ledger）。
4. 资产治理（Asset Governance）。
5. 进化提案入口（Evolution Intake, Minimal）。

### 2.2 Out of Scope（当前不做）

1. 大规模业务 Agent/业务流程覆盖。
2. 复杂自动调度、并发优化与性能极限优化。
3. 跨系统深度耦合集成与重权限细化工程。

## 3. 目标用户与使用者

1. 组织治理者（Founder/CTO/平台负责人）：关注可控性、可审计性、迭代效率。
2. 流程负责人（Architect/BPM Owner）：关注流程定义质量、门禁稳定性、回滚能力。
3. 执行角色（Agent Operator/开发者）：关注输入输出契约明确、失败可恢复。

## 4. 产品目标（Phase 1/2）

1. 让至少 1 条元流程在本地可运行到 Verify 阶段并完成门禁裁决。
2. 让流程执行全链路可追溯、可回放、可审计。
3. 让流程资产具备可注册、可版本化、可治理的发布能力。
4. 让运行反馈可进入改进提案流，形成最小进化闭环入口。

## 5. 成功指标

### 5.1 North Star

1. Objective Lead Time。
2. Process First Pass Yield。
3. Process Reuse Rate。

### 5.2 Guardrail

1. Change Failure Rate。
2. MTTR for Process Change。
3. Human Intervention Ratio。
4. Evidence Completeness。

## 6. Epic 与需求清单

## 6.1 Epic A：Process Runtime（流程执行最小闭环）

### A-FR-001 流程实例创建与状态流转

需求：

1. 系统必须支持创建流程实例（`instance_id` 唯一）。
2. 系统必须支持状态机：`Created -> Running -> Waiting -> Completed/Failed/Cancelled -> Archived`。
3. 每次状态变更必须记录 `timestamp`、`phase_id`、`actor`、`reason`。

验收标准：

1. 能看到至少 1 个完整实例状态流转记录。
2. 状态流转日志可通过路径追溯到对应证据文件。

### A-FR-002 Phase 调度与原子流程约束

需求：

1. BPM 必须按 `process.json` 的 Phase 顺序/控制结构进行调度。
2. 原子流程必须满足 `Atomic = (Actor, Skill, Input, Output, SIPOC metadata)`。
3. I/O 校验失败时必须拒绝流转并返回责任 Actor。

验收标准：

1. 至少 1 个 Phase 因 I/O 校验失败被拒绝并记录失败证据。
2. 同一流程在修复后可重新提交并继续推进。

### A-FR-003 失败恢复与升级链

需求：

1. 可重试错误采用有限重试策略。
2. 不可重试错误立即失败并触发回滚预案。
3. 升级链遵循：`actor -> owner -> BPM -> admin`。

验收标准：

1. 至少 1 次失败场景触发升级链并有完整记录。
2. 失败流程能输出可执行的 next actions。

## 6.2 Epic B：Governance Gate（验证与门禁）

### B-FR-001 Verify 门禁输入约束

需求：

1. Verify 仅消费 `normalized_verdict`。
2. Scenario 原始结果不得直接作为门禁输入。
3. 归一化失败时必须 Fail-Closed。

验收标准：

1. 成功场景可出具 `pass/confidence/remarks/suggestions`。
2. 失败场景下门禁拒绝且可追溯拒绝原因。

### B-FR-002 Fail-Closed 守卫

需求：

1. 缺失关键证据时默认拒绝发布。
2. verdict 不可解析时默认拒绝流转。
3. Verify 超时且无替代证据时默认失败。

验收标准：

1. 至少 1 次触发 Fail-Closed 并写入 `guard_log`。
2. 门禁决策包含明确 `decision` 与 `reason` 字段。

### B-FR-003 测试定位与叙事约束

需求：

1. 测试能力定位为治理子系统，不作为产品核心定位。
2. 发布口径必须体现“流程价值交付”而非“测试能力堆叠”。

验收标准：

1. 产品文档主线以流程资产与业务价值为中心。
2. 测试文档在定位描述上与 SSOT 一致。

## 6.3 Epic C：Evidence Ledger（证据账本）

### C-FR-001 证据最小集合

需求：

1. 每个 Phase 至少落盘 `input_ref`、`output_ref`、`log_ref`、`decision`。
2. Verify 阶段必须落盘：`transcript`、`raw_result`、`normalized_verdict`、`fail_closed_guard_log`。
3. 所有证据路径必须可解析并推荐绝对路径引用。

验收标准：

1. 任意流程实例可回放证据链并复现门禁结论。
2. 任意关键字段缺失时能触发拒绝流转。

### C-FR-002 上下文交接协议

需求：

1. 跨 Phase 交接必须包含 `objective_ref`、`phase_id`、`input_ref`、`output_ref`、`acceptance_criteria`、`known_risks`、`next_actions`。
2. 未落盘关键结论视为不存在。

验收标准：

1. 随机抽检至少 1 条实例链路满足最小字段要求。
2. 协议违规时 BPM 拒绝流转并记录违规事件。

## 6.4 Epic D：Asset Governance（资产治理）

### D-FR-001 registry 一致性

需求：

1. Agent/Skill/Process 资产必须可在 registry 查询。
2. registry 关键字段需与 `SKILL.md` frontmatter 对齐。
3. Active 资产变更必须同步版本记录与变更记录。

验收标准：

1. 至少 1 个新增/更新资产完成 registry 同步校验。
2. 字段不一致时发布流程应被阻断或标记为治理违规。

### D-FR-002 生命周期治理

需求：

1. 生命周期状态统一为：`Draft -> Review -> Active -> Deprecated -> Retired`。
2. 状态迁移必须绑定输入约束、验证动作、证据产物、负责人、回滚路径。

验收标准：

1. 至少 1 次状态迁移具备完整五要素记录。
2. 缺失任一要素时不允许进入 `Active`。

## 6.5 Epic E：Evolution Intake（最小进化入口）

### E-FR-001 改进提案登记

需求：

1. 运行反馈可转化为标准化改进提案。
2. 提案至少包含：问题定义、收益假设、风险假设、影响范围、验证方案。
3. 高风险提案必须挂载人类审批断路器。

验收标准：

1. 至少 1 条提案记录能追溯到触发证据。
2. 缺失回滚预案的提案不得进入发布阶段。

## 7. 非功能性需求（NFR）

1. 可审计性：关键决策必须可追溯到证据路径。
2. 一致性：文档、流程定义、registry 与运行态字段一致。
3. 可恢复性：失败场景必须定义恢复或回滚路径。
4. 可扩展性：在不破坏契约下支持新增 Skill/Process。
5. 可维护性：每次变更后施工平面必须同步更新。

## 8. 发布计划

### 8.1 Release R1（Phase 1 对齐）

交付内容：

1. Epic A、B、C 的最小可用能力上线。
2. Epic D 的基本校验链路可执行。
3. 至少 1 条元流程具备端到端证据回放能力。

发布门槛：

1. Verify 门禁可稳定输出标准 verdict。
2. Fail-Closed 在关键失败场景下生效。
3. Evidence Completeness 达到基线要求（关键文件齐全）。

### 8.2 Release R2（Phase 2 对齐）

交付内容：

1. 系统基于自身流程上线至少 1 个新 Skill。
2. Epic E 提供最小可用进化提案入口并闭环 1 次改进。
3. 资产治理覆盖发布前后一致性校验。

发布门槛：

1. 新 Skill 具备 Objective/Spec/Test/Development/Evidence 全链路证据。
2. 至少 1 次改进提案通过验证并产生可观测收益。

## 9. 验收与追踪矩阵（需求 -> 证据）

1. A-FR-001/A-FR-002/A-FR-003 -> 流程实例 `state.json` + Phase 证据目录。
2. B-FR-001/B-FR-002 -> `normalized_verdict.json` + `fail_closed_guard_log`。
3. C-FR-001/C-FR-002 -> `context.md` + `input/output/log` + 交接字段抽检记录。
4. D-FR-001/D-FR-002 -> registry 对齐记录 + 生命周期迁移记录。
5. E-FR-001 -> 提案文档 + 关联运行证据 + 审批记录。

## 10. 依赖、风险与缓解

1. 依赖：OpenClaw CLI 与 gateway 能稳定运行。  
   缓解：上线前执行 `health` 与配置一致性检查。
2. 风险：需求扩张快于治理能力建设。  
   缓解：严格遵守 Phase In/Out Scope。
3. 风险：文档化不足导致审计断链。  
   缓解：执行“未落盘即不存在”与施工平面回写纪律。
4. 风险：过度强调测试导致产品定位漂移。  
   缓解：评审时优先检查流程价值与业务指标映射。

## 11. 开放问题

1. Objective Lead Time 的基线采样窗口在 Phase 1 采用周还是双周。
2. Process Reuse Rate 的最小统计口径（按流程数或按执行次数）。
3. Evolution Intake 的提案模板是否需要纳入 registry 契约字段。

## 12. 关联文档

1. `/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md`
4. `/Users/albus/MyProjects/ANC_v2/docs/architecture/context_protocol.md`
5. `/Users/albus/MyProjects/ANC_v2/docs/architecture/registry_contracts.md`
6. `/Users/albus/MyProjects/ANC_v2/docs/architecture/product_brief.md`
7. `/Users/albus/MyProjects/ANC_v2/docs/architecture/product_design_blueprint.md`
8. `/Users/albus/MyProjects/ANC_v2/docs/architecture/construction_plane.md`
