# Meta 资产质量差距矩阵（P0 基线）

> change: `m3-meta-asset-quality-hardening`

| 设计条目 | 应有资产 | 现状 | 阻断级别 | 归属 Phase | 状态 | 验收条件 |
|---|---|---|---|---|---|---|
| `ap-*-bundle` 退役 | P5 子流程库 + 主流程替换 | bundle 仍在主流程调用链中 | S0 | P2 | open | 主流程 manifest 中 bundle 引用归零 |
| 流程拆分方法论缺失 | 流程方法论标准文档 | 尚无 MECE/金字塔/SRP/DIP/LoD 统一规范 | S0 | P1 | open | 新标准落盘并纳入设计入口 |
| 子流程划分反例未制度化 | 反模式清单 + fail-closed 判据 | 仅有原则，无反例约束 | S1 | P1 | open | 反例写入标准与 spec requirement |
| Meta 核心技能契约深度不足 | `agent/process/template/skill-creator` 升级契约 | 结构可用但运行约束不完整 | S0 | P3 | open | 输入输出字段级约束 + fail-closed 决策表完整 |
| Meta 非核心技能执行手册不足 | `objective/spec/test-designer/llm-judge` 升级 | 用例与运行入口偏薄 | S1 | P3 | open | 每个技能具备执行步骤/references/5+用例 |
| skill-creator 同名冲突 | 本地唯一运行名 + 映射说明 | openclaw managed 同名覆盖本地语义 | S0 | P3 | open | openclaw 可唯一解析本地版本 |
| 设计/清单/registry 联动不完整风险 | 全量联动更新 | 容易出现“先改实现后补文档”倒挂 | S0 | P4 | open | 设计 + inventory + registry + construction 同步通过 |
| QA 在线主验收机制不足 | 在线套件与证据结构 | 现有以静态门禁为主 | S0 | P5 | open | openclaw 在线 case 成为主验收项 |
| 在线缺陷闭环流程未固化 | 执行-修复-回归闭环记录 | 尚未形成 Meta 专项机制 | S1 | P6 | open | 缺陷清单与回归证据完整 |
| 生命周期收口策略 | 仅到 `review` 的治理规则 | 历史回合中有状态漂移风险 | S0 | P7 | open | 全量资产状态收敛到 review，active=0 |

## P1 迁移矩阵（执行级，冻结）

| 待淘汰 bundle | 替代 P5 子流程 ID | AP 语义边界 | 输入契约 | 输出契约 | 调用方流程 | 迁移顺序 | 兼容期与退役策略 | 重叠解释/解耦说明 |
|---|---|---|---|---|---|---|---|---|
| `ap-004-bundle` | `spec-authoring-contract` | AP-004 | `objective_ref`, `scope_baseline_ref` | `spec_ref` | `full-development.p2`, `refactor.p2` | 1 | 同回合 `deprecated -> retired` | 作为唯一规格产出语义，禁止被其它子流程内联重写 |
| `ap-006-bundle` | `implementation-execution-core` | AP-006 | `spec_ref`, `test_plan_ref` | `implementation_ref` | `full-development.p4`, `hotfix.p4`, `refactor.p4` | 2 | 同回合 `deprecated -> retired` | 只负责实现执行，不承载验证/发布语义 |
| `ap-012-bundle` | `release-packaging-governed` | AP-012 | `candidate_artifacts_ref`, `final_gate_verdict_ref`, `lifecycle_transition_ref`, `registry_sync_ref` | `release_package_ref`, `changelog_ref`, `release_decision`, `rollback_bundle_ref` | `full-development.p7`, `hotfix.p7` | 3 | 同回合 `deprecated -> retired` | 发布语义独占，禁止与演化规划混合 |
| `ap-001-002-bundle` | `hotfix-intake-normalization` | AP-001 + AP-002（hotfix profile） | `incident_context_ref` | `hotfix_objective_ref`, `impact_scope_ref`, `rollback_direction_ref` | `hotfix.p1` | 4 | 同回合 `deprecated -> retired` | 与通用 intake 的重叠通过 incident profile 隔离 |
| `ap-001-002-003-bundle` | `objective-scope-baseline` | AP-001 + AP-002 + AP-003（normal/refactor profile） | `objective_context_ref` | `objective_ref`, `scope_baseline_ref` | `full-development.p1`, `refactor.p1` | 5 | 同回合 `deprecated -> retired` | 与 hotfix intake 的 AP-001/002 重叠由 profile + 调用方边界解耦 |
| `ap-013-014-015-017-bundle` | `evolution-feedback-planning` | AP-013 + AP-014 + AP-015 + AP-017 | `feedback_evidence_ref` | `improvement_plan_ref`, `retro_report_ref` | `full-development.p8` | 6 | 同回合 `deprecated -> retired` | 仅演化反馈，不承载发布/生命周期迁移 |
| `ap-003-004-bundle` | `hotfix-scope-spec-baseline` | AP-003 组合 `spec-authoring-contract`（AP-004 不重复定义） | `hotfix_objective_ref`, `impact_scope_ref` | `hotfix_scope_baseline_ref`, `hotfix_spec_ref` | `hotfix.p2` | 7 | 同回合 `deprecated -> retired` | 通过组合层解耦 AP-004，避免与 `spec-authoring-contract` 语义重叠 |

### P1 Fail-Closed 判据

1. 若迁移矩阵存在一对多/多对多责任重叠且未解释，Phase1 判定失败。
2. 若任何文档仍把 bundle 作为目标态运行结构，Phase1 判定失败。
