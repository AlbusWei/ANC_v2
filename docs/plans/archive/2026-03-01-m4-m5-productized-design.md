# M4/M5 产品化生命周期与自演化设计（内部产品优先）

> Status: Superseded
> Superseded-By: `docs/plans/SSOT-design.md`
> Superseded-On: 2026-03-01

> 日期：2026-03-01
> 适用范围：`docs/design/modules/M4-lifecycle-management.md`、`docs/design/modules/M5-self-evolution.md`

## 1. 背景与目标

当前 M1/M2/M3/M6 已具备自开发与工程化执行能力，但 M4/M5 仍偏“资产治理最小版”。本设计将 M4/M5 升级为“产品中心”治理：

1. 以**内部产品**作为唯一治理语义单元。
2. 资产（skill/process/agent）仅作为产品实现材料，不独立成为治理目标。
3. 支持**同一产品多版本实例并存**（active/developing/legacy 并行）。
4. 引入 M5 的“周期 + 事件”混合触发演化闭环。

## 2. 关键决策（已确认）

1. 优先对象：内部产品（A）。
2. 治理粒度：产品级（B）；单资产可作为单产品，但语义仍是“产品”。
3. 准入最小定义：
   - 目标（Goal）
   - 消费者/用户（Consumer）
   - 场景边界（Scope）
   - 验收标准（Acceptance）
   - 版本策略（Version Policy）
4. 生命周期模型：必须体现迭代 loop，不能线性一次流转。
5. 版本主键：`branch/worktree` 优先（B），语义版本可选附加。
6. M4 治理对象：版本实例（A）。
7. M5 触发策略：混合触发（C）= 周期保底 + 事件插队。

## 3. 总体架构

### 3.1 领域对象

1. `Product`：内部产品定义，包含目标与边界。
2. `ProductVersionInstance`：产品在 branch/worktree 上的版本实例，作为生命周期治理对象。
3. `ProductAssetBinding`：版本实例到 skill/process/agent 的绑定清单。
4. `EvolutionProposal`：M5 产生的演化提案（收益假设、风险、验证口径、回滚策略）。
5. `VersionRoleTag`：版本角色标记（如 `developing | active | legacy`），允许同产品多实例并存。

### 3.2 M4 / M5 边界

- M4：
  - 治理 `ProductVersionInstance` 的状态迁移与审批证据。
  - 管理版本实例角色与切换约束。
  - 确保产品定义与实现绑定的一致性。
- M5：
  - 监控、分析并触发演化提案。
  - 将提案编排进 M3 执行，调用 M1 验证，再回到 M4 放行。
  - 不直接替代生命周期审批执行。

## 4. 生命周期与并存模型

### 4.1 版本实例状态循环（非线性）

建议定义为循环域：

`idea -> design -> build -> verify -> operate -> observe -> evolve -> (回到 design/build)`

并保留治理终止路径：`deprecate -> retire`。

### 4.2 多版本并存规则

1. 同一 `product_id` 可有多个 `ProductVersionInstance`。
2. 每个实例独立状态推进。
3. 同时允许：
   - 1 个或多个 `active` 候选（按策略约束）
   - 若干 `developing`
   - 若干 `legacy`
4. 版本切换必须有证据链：验证结果、风险评估、回滚策略。

## 5. M4 设计增强点

1. 从“资产状态机”升级为“版本实例治理机”。
2. 增加产品定义准入校验：无 Goal/Consumer/Scope/Acceptance/Version Policy 则 fail-closed。
3. 增加版本实例角色变更治理：`developing -> active`、`active -> legacy`、`legacy -> retired`。
4. 保持高风险审批链（`hr -> admin`）不变，但明确针对“版本实例切换”。

## 6. M5 设计增强点

1. 混合触发引擎：
   - 周期触发：固定巡检节奏
   - 事件触发：事故、质量下降、需求变化插队
2. 演化提案必须可追溯：
   - 改进目标
   - 预期收益与验证指标（可逐步强化，不强制立项时完整）
   - 风险与回滚
3. 演化执行闭环：
   - M5 产提案
   - M3 实施到新版本实例
   - M1 验证
   - M4 放行并切换角色

## 7. 与现有体系兼容策略

1. 保留当前资产 5 态生命周期（draft/review/active/deprecated/retired）用于 registry 层。
2. 新增“产品版本实例生命周期”作为 M4 专属语义层，不与 registry 5 态冲突。
3. M4/M5 文档先落“设计与接口契约”，实现资产在后续计划分批落地。

## 8. 首轮落地范围（YAGNI）

1. 必做：
   - M4/M5 模块文档重写（产品中心）
   - 新增产品版本治理协议文档
   - 新增产品生命周期数据模型文档
   - 施工平面与依赖矩阵同步
2. 暂不做：
   - 一次性新增完整运行时引擎实现
   - 大规模新增 registry 字段
   - 强制语义版本治理

## 9. 验收口径（设计阶段）

1. 文档中“产品中心语义”与“版本实例治理”一致、无资产中心残留歧义。
2. 明确支持多版本并存与迭代 loop。
3. M4/M5 与 M1/M2/M3/M6 协作边界清晰。
4. 同步更新 construction plane 与相关 inventory/接口/数据模型文档引用。
