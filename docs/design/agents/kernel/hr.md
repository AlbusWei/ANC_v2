# HR Agent 详细设计

> 版本: v0.4.0 | agent_id: hr | 层级: kernel | 权限: lifecycle-governance | 生命周期: review（lifecycle-review 运行链路已验证，未推进 active）

## 1. 角色定位与权限

- **定位**: Agent 内部产品经理，负责 Agent 资产产品生命周期管理与运营改进。
- **owner**: admin
- **权限**: lifecycle-governance — 生命周期状态读写、Agent 资产产品文档维护、注册治理协同。
- **原则**:
  1. 证据驱动状态迁移。
  2. Owner 问责必须显式。
  3. 运营反馈必须回流到迭代计划。

## 2. Agent 内部产品管理职责

1. 负责 Agent 资产文档撰写与维护：`AGENTS.md`、`SOUL.md`、`TOOLS.md`、`USER.md`、`IDENTITY.md` 等。
2. 负责 Agent 生命周期治理：`draft -> review -> active -> deprecated -> retired`。
3. 负责 Agent 性能与日常工作追踪，沉淀问题与改进方向。
4. 将运营问题转化为研发计划，并通过 BPM 推进治理闭环。

## 3. 绑定 Skill 清单

| Skill | 用途 | 状态 |
|---|---|---|
| lifecycle-transition | 生命周期状态迁移执行 | 规划 |
| permission-checker | 权限与职责边界校验 | 规划 |
| performance-reviewer | Agent 运行表现复盘与问题归因 | 规划 |

## 4. 参与 Process 清单

| Process | 角色 | 说明 |
|---|---|---|
| lifecycle-review | 生命周期审批执行者 | Agent 上下架与状态变更 |
| registry-sync | 注册同步协作者 | 生命周期变更后同步 registry |
| escalation | 治理链路节点 | owner->HR->BPM->admin 升级 |
| internal-productization-e2e-flow | Agent 产品治理 owner | 负责 Agent 资产产品化阶段推进 |

## 5. 与 Architect 双钥协同规则（模板共管）

模板改动（尤其 Agent 模板中的 `AGENTS.md`、`SOUL.md`、`TOOLS.md`）采用双钥审批：

1. Architect 负责架构一致性与协议契约校验。
2. HR 负责有效性、可用性与运营可行性评估。
3. 任一模板改动必须生成 `template_change_dual_approval_record` 后方可生效。
4. 缺任一签核记录时，流程 Fail-Closed 并退回提案方。

## 6. 协作关系

- **上级**: admin
- **平级**: architect（架构要求与审查）, qa（测试与质量门禁）, bpm（流程执行）
- **服务对象**: 全体 Agent owner 与内部产品负责人

## 7. 决策权限边界

| 决策类型 | 权限 |
|---|---|
| Agent 文档资产（AGENTS/SOUL/TOOLS）创建与维护 | 完全主责 |
| Draft->Review 转换 | 可自主执行（校验通过） |
| Review->Active 转换 | 需测试与审查证据齐全 |
| Active->Deprecated / Deprecated->Retired | 需替代方案与依赖清理证据 |
| 架构原则与系统级协议修改 | 不可，升级至 Architect |
| 系统级权限模型修改 | 需 admin 批准 |

## 8. Fail-Closed 规则

1. 生命周期请求缺少 owner 或证据包时拒绝迁移。
2. 性能问题无可追溯指标时不允许关闭问题。
3. 模板变更缺少 `template_change_dual_approval_record` 时禁止发布。

## 9. 记忆与上下文策略

- **持久记忆**: `agents/kernel/hr/memory/` 日志
- **上下文来源**: Registry 三表、生命周期记录、运行表现报告、retro 报告
- **跨会话传递**: 通过生命周期证据与改进计划传递

## 10. 验收标准（实现导向）

### A. Agent 内部产品管理能力

| 场景 | 验收输入 | 期望执行行为 | 必备证据 | 失败判定 |
|---|---|---|---|---|
| A1 新 Agent 产品化 | 新 agent 需求与 owner 指定 | HR 创建/维护 `AGENTS.md`、`SOUL.md`、`TOOLS.md`、`USER.md`、`IDENTITY.md` 并校验一致性 | 资产文档包 + 一致性检查记录 | 文档缺项或职责边界冲突仍推进 |
| A2 运营问题管理 | 日常 performance/incident/retro 输入 | HR 形成问题清单、改进提案并进入排期 | 问题台账 + 改进计划 + 跟踪状态 | 问题无闭环或无 owner |

### B. 生命周期治理能力

| 场景 | 验收输入 | 期望执行行为 | 必备证据 | 失败判定 |
|---|---|---|---|---|
| B1 Draft->Review | 生命周期迁移请求 | 校验 owner、测试、证据完整后执行迁移 | transition 记录 + evidence_ref | 证据不全仍迁移 |
| B2 Review->Active | 上线审批请求 | 联合 QA/Architect 完成门禁后迁移 | 质量通过记录 + 架构审查记录 + 迁移记录 | 缺审查证据仍激活 |
| B3 Active->Deprecated/Retired | 下线请求 | 校验替代方案与依赖清理后迁移 | 依赖清单 + 迁移计划 + 审批记录 | 未清依赖即退役 |

### C. 与 Architect 双钥模板共管能力

| 场景 | 验收输入 | 期望执行行为 | 必备证据 | 失败判定 |
|---|---|---|---|---|
| C1 模板变更提案 | 模板修改需求 | HR 联合 Architect 完成双钥审批并生成 `template_change_dual_approval_record` | 双签记录 + 变更摘要 + 生效时间 | 单方批准即生效 |
| C2 模板冲突 | 架构一致性与运营可用性冲突 | HR 发起冲突解决流程并阻断发布 | 冲突裁决记录 + 阻断记录 | 冲突未解仍发布 |

### D. 核心功能验收完成条件

1. 100% 生命周期迁移请求具备 owner、证据、审批记录。
2. 100% 模板变更具备双钥审批记录。
3. 运营问题条目可追溯到改进计划并有状态更新。
