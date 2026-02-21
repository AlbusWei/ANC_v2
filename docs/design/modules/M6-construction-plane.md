# M6 — 施工面模块详细设计

> 版本: v0.7.0 | 建设优先级: P0 | 最后更新: 2026-02-21

## 模块定位

`M6` 是 ANC 的施工治理中枢，负责把“建设计划、联动门禁、证据归档、开放问题”统一到一个可审计平面。  
`M6` 的模块 owner 固定为 `architect`，`bpm` 负责流程编排执行，`system-analyst` 负责巡检诊断输入。

相关文档：

1. `docs/architecture/construction_plane.md`
2. `docs/design/modules/module-dependency-matrix.md`
3. `docs/design/skills/construction-plane-skills.md`
4. `docs/design/processes/construction-plane-governance-process.md`
5. `docs/design/interfaces/openspec-collaboration-protocol.md`

## Phase 1 成功优先级

1. 文档级设计先行：先把治理契约、协作边界、同步机制定义清晰，再进入运行级验证。
2. 联动门禁可执行：module/layer 变化能触发 design + inventory + registry + 施工平面同回合闭合。
3. 语义一致性优先：通过 Architect 主责 + OpenSpec 协同防止语义漂移。
4. 开放问题可治理：未决项必须带 owner、阶段与下一步，不允许隐性搁置。

## 模块边界

1. `M6` 负责建设期治理，不负责运行时流程调度（`M2`）与生命周期审批（`M4`）。
2. `M6` 可以触发治理流程与联动审计，但不替代模块内专业评测能力（`M1`）。
3. `M6` 的状态更新必须基于已落盘证据，禁止口头结论直写 Done。
4. `M6` 不引入业务旁路，所有资产变更仍按各模块 canonical 路径落盘。

## Ownership 与协作模型

1. 模块 owner：`architect`（对 M6 语义一致性与协议演进负最终责任）。
2. 执行编排：`bpm`（负责把 M6 治理流程实例化并完成门禁执行）。
3. 巡检输入：`system-analyst`（基于运行/评审信号触发可调频巡检，优先降低遗漏风险）。
4. 结果闭环：`architect` 对巡检结论做架构裁决，`bpm` 回填施工平面与证据索引。

## 组件与落盘状态

| 组件 | 目标资产 | 状态 |
|---|---|---|
| construction board | `docs/architecture/construction_plane.md` | 已落盘（active） |
| linkage auditor | `sys.arch.construction-audit` | 本轮新增（draft） |
| openspec sync executor | `system.integration.openspec-sync` | 本轮新增（draft） |
| governance flow | `construction-plane-governance` | 本轮新增（draft） |
| OpenSpec sync protocol | `docs/design/interfaces/openspec-collaboration-protocol.md` | 本轮新增（draft） |
| OpenSpec sync schema | `docs/design/data-models/openspec-collaboration-schema.json` | 本轮新增（draft） |
| dependency baseline | `docs/design/modules/module-dependency-matrix.md` | 已落盘（active） |
| module detailed spec | `docs/design/modules/M6-construction-plane.md` | 本轮重构（v0.7.0） |

## 流程连续性模型

1. 范围基线段：`scope-intake-and-baseline`（AP-001/002/003 语义映射）。
2. 联动审计段：`run-construction-audit`（审计缺口与阻断项）。
3. 联动补齐段：`execute-linked-updates`（文档、inventory、registry 同步）。
4. OpenSpec 同步段：`sync-openspec-state`（生成结构化 `openspec_sync_ref`）。
5. 收口校验段：`verify-and-close`（`registry_contract_tool.py verify` + 开放问题落盘）。
6. 连续性约束：单复合流程只覆盖施工治理连续段，不跨非连续生命周期断点。
7. phase 闭合约束：每个 phase 必须映射到已定义 skill 或已定义子流程。

## Hybrid OpenSpec 协同契约

1. Hybrid 原则：ANC 本地设计文档负责治理契约与落盘真相；OpenSpec 负责协同提案、评审线程与变更对齐。
2. 同步方向：采用“双向引用、单点裁决”模式。
   - 本地文档记录 `openspec_ref` 与决议快照。
   - OpenSpec 记录对应 ANC 文档路径与版本锚点。
3. 裁决权：当两侧语义冲突时，以 `architect` 在 ANC 文档落盘的裁决为准，再回写 OpenSpec。
4. 禁止项：禁止仅更新 OpenSpec 而不更新 ANC 设计文档；禁止仅更新 ANC 而不回填 OpenSpec 映射。
5. 完整 Schema：同步记录必须满足 `openspec-collaboration-schema.json`，禁止只保留最小字段。

## 输入契约（施工回合输入包）

1. `round_goal`
2. `change_scope_ref`
3. `changed_assets`
4. `linkage_targets`
5. `owner`
6. `openspec_ref`（架构相关变更必填）

## 输出契约（施工回合输出包）

1. `m6_update_bundle_ref`
2. `linkage_report_ref`
3. `openspec_sync_ref`
4. `registry_verify_report_ref`
5. `construction_plane_delta_ref`
6. `open_questions_ref`

## 依赖关系（类型化）

1. 观测 `M2`（`E`）：消费流程实例与运行证据，用于进度与风险判断（非阻断前置）。
2. 观测 `M1`（`E`）：消费质量门禁结果，用于里程碑判定（非阻断前置）。
3. 观测 `M4`（`G/E`）：消费生命周期状态与审批证据（非阻断前置）。
4. 依赖 `OpenSpec`（`E/G`）：消费协同评审状态并回写 ANC 裁决与映射。
5. 输出给 `M1/M2/M3/M4/M5`（`E`）：提供统一施工状态、风险与开放问题上下文。

## Fail-Closed 规则

1. 受影响资产未形成联动清单，禁止回合关闭。
2. design/inventory/registry 任一缺项，施工状态不得标记为 Done。
3. `registry_contract_tool.py verify` 失败，默认阻断并升级 `actor -> owner -> bpm -> admin -> human`。
4. 开放问题缺失 owner 或下一步，禁止从 In Progress 迁移到 Done。
5. 架构相关变更缺失 `openspec_ref` 或双向映射，禁止回合关闭。
6. OpenSpec 与 ANC 文档语义冲突且未形成 architect 裁决，禁止推进。

## 风险与缓解

1. 风险：模块文档先更新，资产联动滞后。
缓解：强制执行 `construction-plane-governance` 流程，并将 verify 结果作为关闭条件。
2. 风险：联动审计依赖人工经验，稳定性不足。
缓解：引入 `sys.arch.construction-audit` 统一审计输入输出契约。
3. 风险：开放问题长期堆积。
缓解：每轮必须给出 owner、阶段与下一步，未满足不得关闭回合。

## 验收清单

- [ ] `construction-plane-governance` 已注册并可被 BPM 调度
- [ ] `sys.arch.construction-audit` 已注册且具备 Capability Contract + test_mount
- [ ] `system.integration.openspec-sync` 已注册并可产出 schema 合法记录
- [ ] 修改 module/layer 设计时，联动门禁可在同回合闭合
- [ ] 施工回合可产出最小证据包并可追溯
- [ ] 开放问题具备 owner、计划阶段与下一步动作
- [ ] 架构相关回合具备 OpenSpec 双向映射且无语义漂移

## 已定决策（2026-02-21）

1. `D-M6-001`：Phase 1 先完成文档级设计与阐释，运行级验证后置。
2. `D-M6-002`：M6 语义 owner 固定为 `architect`，优先防止语义漂移。
3. `D-M6-003`：巡检采用“变更触发 + system-analyst 可调频巡检”，前期优先降低遗漏风险。

## 新增开放问题（需后续决策）

1. `Q-M6-005`：巡检调频阈值采用哪一组主指标（变更密度/风险等级/未决项数量）作为主触发？
