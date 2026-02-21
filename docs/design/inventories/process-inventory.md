# Process 全量清单

> 版本: v0.3.0 | SSOT 上游: `/Users/albus/MyProjects/ANC_v2/shared/registry/process_registry.json`

## Canonical Process Paths

| process_id | canonical_path | status |
|---|---|---|
| development-process | `/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/` | canonical |
| governed-config-change | `/Users/albus/MyProjects/ANC_v2/processes/meta/governed-config-change/` | canonical |

## Legacy Paths

| path | status | 说明 |
|---|---|---|
| `/Users/albus/MyProjects/ANC_v2/processes/development-process/` | legacy | Phase 0.5 历史路径，仅保留参考，不再作为 registry 真相源 |

## 已注册 Process

| process_id | 名称 | 类型 | owner | 阶段数 | 状态 | 路径 |
|---|---|---|---|---|---|---|
| development-process | development-process | 复合 | bpm | 4 | draft | `/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/` |
| governed-config-change | governed-config-change | 复合 | bpm | 5 | draft | `/Users/albus/MyProjects/ANC_v2/processes/meta/governed-config-change/` |

## 规划中 Process — 元流程

| process_id | 类型 | 规划阶段 | 用途 |
|---|---|---|---|
| full-development | 复合 | Phase 2 | 全链路开发流程 |
| hotfix | 复合 | Phase 2 | 紧急修复 |
| refactor | 复合 | Phase 2 | 重构流程 |

## 规划中 Process — 治理流程

| process_id | 类型 | 规划阶段 | 用途 |
|---|---|---|---|
| lifecycle-review | 复合 | Phase 1 | 生命周期审批 |
| registry-sync | 原子 | Phase 1 | 注册表同步 |
| escalation | 复合 | Phase 1 | 异常升级 |

## 规划中 Process — 演化流程

| process_id | 类型 | 规划阶段 | 用途 |
|---|---|---|---|
| evolution-loop | 复合 | Phase 4 | 演化闭环 |
| health-check | 复合 | Phase 4 | 健康检查 |
| improvement-review | 复合 | Phase 4 | 改进评审 |

## P6 原子流程目录

详见 `/Users/albus/MyProjects/ANC_v2/docs/design/processes/p-levels/P6-atomic-process-catalog.md`。

## 校验规则

1. inventory 路径必须与 registry 一致。
2. legacy 路径不得作为新流程注册来源。
3. 所有状态变更遵循 5 态生命周期。
