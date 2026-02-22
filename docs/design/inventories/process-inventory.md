# Process 全量清单

> 版本: v0.9.0 | SSOT 上游: `shared/registry/process_registry.json`

## Canonical Process Paths

| process_id | canonical_path | status |
|---|---|---|
| development-process | `/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/` | canonical |
| full-development | `/Users/albus/MyProjects/ANC_v2/processes/meta/full-development/` | canonical |
| hotfix | `/Users/albus/MyProjects/ANC_v2/processes/meta/hotfix/` | canonical |
| refactor | `/Users/albus/MyProjects/ANC_v2/processes/meta/refactor/` | canonical |
| governed-config-change | `/Users/albus/MyProjects/ANC_v2/processes/meta/governed-config-change/` | canonical |
| construction-plane-governance | `/Users/albus/MyProjects/ANC_v2/processes/meta/construction-plane-governance/` | canonical |
| trigger-schedule-runtime | `/Users/albus/MyProjects/ANC_v2/processes/control/trigger-schedule-runtime/` | canonical |
| trigger-event-runtime | `/Users/albus/MyProjects/ANC_v2/processes/control/trigger-event-runtime/` | canonical |

## Legacy Paths

| path | status | 说明 |
|---|---|---|
| `/Users/albus/MyProjects/ANC_v2/processes/development-process/` | legacy | Phase 0.5 历史路径，仅保留参考，不再作为 registry 真相源 |

## 已注册 Process

| process_id | 名称 | 类型 | owner | 阶段数 | 状态 | 路径 |
|---|---|---|---|---|---|---|
| development-process | development-process | 复合 | bpm | 4 | draft | `/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/` |
| full-development | full-development | 复合 | bpm | 8 | draft | `/Users/albus/MyProjects/ANC_v2/processes/meta/full-development/` |
| hotfix | hotfix | 复合 | bpm | 7 | draft | `/Users/albus/MyProjects/ANC_v2/processes/meta/hotfix/` |
| refactor | refactor | 复合 | bpm | 6 | draft | `/Users/albus/MyProjects/ANC_v2/processes/meta/refactor/` |
| governed-config-change | governed-config-change | 复合 | bpm | 5 | draft | `/Users/albus/MyProjects/ANC_v2/processes/meta/governed-config-change/` |
| construction-plane-governance | construction-plane-governance | 复合 | architect | 5 | review | `/Users/albus/MyProjects/ANC_v2/processes/meta/construction-plane-governance/` |
| trigger-schedule-runtime | trigger-schedule-runtime | 复合 | bpm | 6 | draft | `/Users/albus/MyProjects/ANC_v2/processes/control/trigger-schedule-runtime/` |
| trigger-event-runtime | trigger-event-runtime | 复合 | bpm | 6 | draft | `/Users/albus/MyProjects/ANC_v2/processes/control/trigger-event-runtime/` |

## 规划中 Process — 元流程

| process_id | 类型 | 规划阶段 | 用途 |
|---|---|---|---|
| quality-gate-preparation | 复合 | Phase 1 | 开发前质量门禁准备流程（AP-005/018/019） |
| quality-gate-evaluation | 复合 | Phase 1 | 实现后质量评测与总聚合流程（AP-007/008/009/020） |

## 规划中 Process — 治理流程

| process_id | 类型 | 规划阶段 | 用途 |
|---|---|---|---|
| lifecycle-review | 复合 | Phase 1 | 生命周期审批 |
| registry-sync | 原子 | Phase 1 | 注册表同步 |
| escalation | 复合 | Phase 1 | 异常升级 |
| hold-governance | 复合 | Phase 1 | HOLD 异常清理与系统健康维护 |
| trigger-runtime-supervisor | 模式（P5） | Phase 1 | 触发运行时上级路由（可选） |
| runtime-policy-calibration | 模式（P5） | Phase 1 | 后验运营分析与策略校准归口 |

## 规划中 Process — 演化流程

| process_id | 类型 | 规划阶段 | 用途 |
|---|---|---|---|
| evolution-loop | 复合 | Phase 4 | 演化闭环 |
| health-check | 复合 | Phase 4 | 健康检查 |
| improvement-review | 复合 | Phase 4 | 改进评审 |

## P6 原子流程目录

详见 `/Users/albus/MyProjects/ANC_v2/docs/design/processes/p-levels/P6-atomic-process-catalog.md`。

新增复合流程设计文档：

1. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/quality-gate-preparation-process.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/quality-gate-evaluation-process.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/hold-governance-process.md`
4. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/trigger-schedule-runtime-process.md`
5. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/trigger-event-runtime-process.md`
6. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/trigger-runtime-supervisor-pattern.md`
7. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/runtime-policy-calibration-process.md`
8. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/full-development-process.md`
9. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/hotfix-process.md`
10. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/refactor-process.md`
11. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/construction-plane-governance-process.md`
12. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/construction-plane-governance-runtime-contract-baseline.md`

新增策略参考文档：

1. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/trigger-runtime-policy-guidelines.md`

## 校验规则

1. inventory 路径必须与 registry 一致。
2. legacy 路径不得作为新流程注册来源。
3. 所有状态变更遵循 5 态生命周期。

## W1 联动备注（M2 BPM Runtime Hardening）

1. 本回合未新增或迁移 Process 生命周期状态。
2. AP-028 输入/输出契约已补齐会话绑定相关字段。

## W2 联动备注（M2 BPM Runtime Hardening）

1. `governed-config-change` 新增可执行 runner：`processes/meta/governed-config-change/scripts/governed_config_change_runner.py`。
2. `governed-config-change` registry 版本由 `0.1.0` 升级到 `0.2.0`，生命周期保持 `draft`。
3. 运行级测试入口：`tests/m2-bpm-runtime/run_tc_gcc.py`，覆盖 `TC-GCC-001~003`。
