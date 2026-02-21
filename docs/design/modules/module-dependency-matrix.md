# 模块依赖矩阵

> 版本: v0.3.0 | 权威顺序来源: `docs/architecture/system_overview.md` §7

## 1. 使用说明

1. 模块建设顺序以 `system_overview.md` 为权威。
2. 本矩阵给出当前阶段的可执行依赖与并行策略，允许随实现进展迭代。
3. 依赖表达采用类型化边，区分运行时依赖与治理/门禁依赖。

## 2. 依赖类型图例

- `R`: Runtime（运行时调度/执行依赖）
- `G`: Governance（生命周期/审批/策略治理依赖）
- `T`: Test Gate（测试与质量门禁依赖）
- `E`: Evidence（证据与审计追溯依赖）

## 3. 建设顺序（SSOT 基线 + 当前并行策略）

SSOT 基线顺序（保持与系统总览一致）：

```
M6 (Construction Plane) → M2 (BPM Engine) → M1 (Test System) → M3 (Self-Dev) → M4 (Lifecycle) → M5 (Self-Evolution)
```

当前阶段实施策略（Phase 1 建议）：

1. 并行轨 A（执行能力）：`M6 -> M2 -> M1 -> M3`
2. 并行轨 B（治理能力）：`M6 -> M2 -> M1 -> M4`
3. 汇合门：`M3 + M4 -> M5`

解释：

1. `M3` 与 `M4` 允许并行建设。
2. `M3` 在 `draft` 级开发可先行；进入 `review/active` 必须通过 `M4` 生命周期门禁。

## 4. 类型化依赖矩阵

行依赖列（`RT` 表示同时依赖 Runtime + Test Gate）：

| | M1 Test | M2 BPM | M3 Self-Dev | M4 Lifecycle | M5 Evolution | M6 Construction |
|---|---|---|---|---|---|---|
| M1 Test | — | RE |  |  |  | E |
| M2 BPM |  | — |  |  |  | E |
| M3 Self-Dev | T | RE | — | G |  | E |
| M4 Lifecycle | T | RE |  | — |  | E |
| M5 Evolution | T | RE | R | G | — | E |
| M6 Construction |  |  |  |  |  | — |

## 5. 模块到资产映射（含本轮新增）

| 模块 | 已落盘关键资产（节选） | 规划/待补资产（节选） | 主要输出给谁 |
|---|---|---|---|
| M1 Test | `llm-judge`, `test-designer`, `TEST` 模板, `registry_contract_tool.py verify` 门禁链 | regression-runner 运行资产化 | M2/M3/M4/M5 |
| M2 BPM | `development-process`, `governed-config-change`, trigger 运行时边界文档 | trigger runtime 可执行资产与证据目录规范 | M3/M4/M5 |
| M3 Self-Dev | `development-process` canonical 路径, 双主线内部开发闭环复用 | `full-development/hotfix/refactor` 可执行流程 | M4/M5/L5 |
| M4 Lifecycle | 统一 5 态治理、registry contract、trigger policy 边界 | `lifecycle-review/registry-sync/escalation` 可执行流程, `trigger_registry` | M3/M5/L2 |
| M5 Evolution | 演化闭环设计、外部反馈复用约束 | `evolution-loop/health-check/improvement-review` 可执行流程 | L3/L5 |
| M6 Construction | `construction_plane.md`, 里程碑与风险登记 | 一致性脚本与周期性审查节奏 | 全模块 |

## 6. 阶段映射与进入条件

| 模块 | 建设阶段 | 优先级 | 最小进入条件 |
|---|---|---|---|
| M6 Construction Plane | Phase 0 | P0 | SSOT/施工平面与更新纪律可执行 |
| M2 BPM Engine | Phase 0-1 | P0 | M6 可追踪 + 流程调度骨架可用 |
| M1 Test System | Phase 0-1 | P0 | M2 可回写证据 + 核心测试能力可复用 |
| M3 Self-Development | Phase 1-2 | P1 | M1 门禁可用 + M2 编排可用 |
| M4 Lifecycle Management | Phase 1 | P1 | M1 门禁可用 + M2 证据链可用 |
| M5 Self-Evolution | Phase 2-4 | P2 | M3 交付反馈可接入 + M4 治理闭环可用 |

## 7. 关键路径与执行风险

关键路径（按并行汇合视角）：

```
(M6 -> M2 -> M1 -> M3) + (M6 -> M2 -> M1 -> M4) -> M5
```

当前主要风险与缓解：

1. 风险：`M3/M4` 并行导致边界漂移。
缓解：以 `M3 draft 先行、review/active 受 M4 门禁` 作为硬规则。
2. 风险：测试能力被各模块重复建设。
缓解：明确 `M1` 作为统一测试与门禁平台，其他模块复用。
3. 风险：流程标准字段与 manifest 漂移。
缓解：在本轮收敛 `process_level/parent_process_id/composed_processes/lineage_policy/control_flow/fail_policy`。

## 8. 触发治理路径与验证锚点

1. 策略面：`M4` 维护 trigger 生命周期、override 与风险规则。
2. 运行面：`M2` 执行触发匹配、去重、补跑、升级与证据归档。
3. 评审锚点：`docs/design/modules/trigger-governance-review-checklist.md`
4. 测试提案：`docs/design/modules/trigger-governance-test-proposal.md`
5. 本轮最小 dry-run 建议：`TG-SCH-002` + `TG-EVT-003`。

## 9. 循环依赖检查

1. 运行时无 `M3 <-> M4` 互锁。
2. `M3 -> M4` 为生命周期门禁依赖，不构成运行时环。
3. 模块图保持 DAG。
