# M1/M3 + M4/M5 从纸面到可执行闭环设计

> Status: Superseded
> Superseded-By: `docs/plans/SSOT-design.md`
> Superseded-On: 2026-03-01

> 日期：2026-03-01
> 范围：`docs/plans/2026-02-27-m1-m3-gate-authenticity-*.md` + `docs/plans/2026-03-01-m4-m5-productized-*.md`

## 1. 背景与问题陈述

当前仓库已经具备部分可运行脚本与回归流程，但存在“设计先行、实现滞后”的断层：

1. **M1/M3 gate-authenticity 未完成 admission-grade 收口**：
   - 已有 `quality_gate_evaluation_runner.py` 等执行骨架。
   - 但缺少集中证据链校验器（计划中的 `verify_gate_evidence_chain`）与对应失败测试。
   - 仍存在 simulated 主观评测路径，且部分默认证据路径仍为 `runtime_data/...`。
2. **M4/M5 产品化当前主要停留在文档语义层**：
   - 已完成产品中心语义、协议、数据模型设计。
   - 尚未在 runtime 层落地 `ProductVersionInstance` 生命周期治理与 `EvolutionProposal` 混合触发执行闭环。

## 2. 目标（本回合）

在不做重型重构的前提下，建立“先可信门禁、后产品化引擎、再端到端联通”的最小可执行闭环：

1. M1/M3：准入结论必须可追溯到真实证据链（缺证据即 fail-closed）。
2. M4：可执行的产品版本实例治理最小 API（状态迁移 + 角色切换）。
3. M5：可执行的混合触发提案流（周期+事件）并可编排回 M3/M1/M4。
4. E2E：至少 1 条“提案 -> 实施 -> 验证 -> 放行”的真实闭环用例。

## 3. 设计原则

1. **先堵漏洞再扩能力**：先完成真实性门禁，再上产品化编排。
2. **Fail-Closed 默认策略**：证据缺失、指标不可比、回滚缺失一律阻断。
3. **YAGNI**：先做最小运行闭环，不引入大规模 schema 变更。
4. **单点判定口径**：门禁判定逻辑集中，避免 runner 分散漂移。
5. **证据可追溯**：输入/输出/命令/phase trace 都有 ref。

## 4. 差距盘点（As-Is -> To-Be）

### 4.1 M1/M3 gate-authenticity

**As-Is**
- 具备运行链路与回归 runner。
- 存在 simulated 主观评测分支。
- 缺集中证据链校验函数与专项失败测试。
- evidence 默认路径策略不统一（`runtime_data/...` 与 `tmp/runtime_data/...` 并存）。

**To-Be**
- 新增统一证据链校验器（OpenClaw trace + phase outputs + representative case report）。
- 在 gate 最终判定前强制执行该校验。
- 新增失败优先测试，覆盖缺 openclaw trace / 缺 phase output / case 非代表性。
- 测试与运行默认 evidence 根统一为 `tmp/runtime_data/...`。

### 4.2 M4/M5 产品化 runtime

**As-Is**
- 产品中心语义与协议文档齐备。
- runtime 仍以资产五态与既有流程为主。
- 未形成 `ProductVersionInstance` 级治理执行器。

**To-Be**
- M4 增加产品版本实例治理执行器：
  - `create_product`
  - `create_version_instance`
  - `transition_version_state`
  - `switch_version_role`
- M5 增加混合触发提案执行器：
  - 周期触发 + 事件触发输入
  - 生成 `EvolutionProposal`
  - 编排到 M3 实施，收集 M1 验证结果，回写 M4 迁移/角色切换。

## 5. 分阶段实施架构（方案一）

### Phase P0（优先级最高）：真实性门禁收口

- 在 M1 gate 聚合点加入集中证据链校验。
- 从“可运行”升级到“可准入”。
- 输出：
  - 失败测试集
  - 证据链校验实现
  - 回归报告（证明 simulated 不能直接通过准入）

### Phase P1：M4 产品版本治理最小执行层

- 在现有 lifecycle-review 语义旁新增产品版本治理执行层（不破坏原有资产五态兼容）。
- 输出：
  - 产品与版本实例最小数据模型（运行态）
  - 状态迁移与角色切换的 fail-closed 规则执行
  - 对应单测/集成测

### Phase P2：M5 混合触发与演化提案执行层

- 实现周期+事件触发入口。
- 统一提案结构并落地编排。
- 输出：
  - 提案生成与优先级最小逻辑
  - M5->M3->M1->M4 串联编排脚本/流程
  - 失败场景（指标不可比、无回滚）阻断测试

### Phase P3：端到端闭环验收

- 构造至少 1 条真实主链路 + 1 条 fail-closed 链路。
- 输出：
  - E2E 证据包
  - 施工平面与 inventory/registry 对账
  - 最终准入结论（自然语言 + 关键证据引用）

## 6. 风险与缓解

1. **历史 simulated 依赖导致回归波动**
   - 缓解：先补测试基线，按 suite 分层替换，禁止一次性全量改动。
2. **M4/M5 新语义与旧资产五态冲突**
   - 缓解：双层语义并存（registry 资产态不变，新增产品版本治理层）。
3. **证据路径迁移影响已有脚本**
   - 缓解：先改默认值 + 保留显式参数覆盖，逐步迁移调用方。

## 7. 验收标准

1. M1 gate 在证据链不完整时必定 fail-closed。
2. M1/M3 关键 runner 默认 evidence 根为 `tmp/runtime_data/...`。
3. M4 可执行 `ProductVersionInstance` 状态迁移与角色切换，且有证据约束。
4. M5 可执行混合触发并产出演化提案，能编排回 M3/M1/M4。
5. 至少 1 条主链 E2E 与 1 条 fail-closed E2E 通过并可审计。

## 8. 优先级建议（用于下一步 implementation plan）

1. **P0 必做**：M1/M3 真实性门禁收口。
2. **P1 必做**：M4 最小治理执行层。
3. **P2 必做**：M5 提案触发与编排最小执行层。
4. **P3 必做**：联合 E2E 验收与文档/平面对账。
