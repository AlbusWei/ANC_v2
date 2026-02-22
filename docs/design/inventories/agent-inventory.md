# Agent 全量清单

> 版本: v0.7.0 | SSOT: `shared/registry/agent_directory.json`

## 已注册 Agent

| agent_id | 层级 | owner | 权限 | 状态 |
|---|---|---|---|---|
| admin | kernel | human | system-root | draft |
| architect | kernel | admin | architecture-governance | draft |
| hr | kernel | admin | lifecycle-governance | draft |
| kernel-dev | kernel | architect | implementation-kernel | draft |
| system-analyst | kernel | admin | system-analysis-governance | active |
| qa | kernel | admin | quality-governance | draft |
| bpm | control | admin | orchestration-control | draft |
| personal-assistant | app | admin | entry-assistance-read-heavy | draft |

## 设计中 Kernel Agents（未注册）

当前无（`system-analyst` 已在 W4 进入已注册清单）。

## 设计中 App Agents（未注册）

### Evolution

monitor, analyst, planner

### Delivery

business-analyst, product-manager, tech-lead, solution-architect, frontend-dev, backend-dev, data-engineer, integration-engineer, qa-engineer, devops-engineer, release-manager-agent, delivery-manager, customer-success-manager

## 职责边界注记

1. `system-analyst` 负责全系统反馈归集与架构级洞察，服务 architect/hr/PM。
2. `app/evolution/analyst` 负责 App/业务层演化分析，不承担系统级架构治理洞察。
3. 所有“需后验运营分析才能形成参数结论”的议题（如 M1 测试时长估计、M2 动态策略校准）由 `system-analyst` 牵头进入 `runtime-policy-calibration` 治理流程，再同步 architect/admin/bpm 决策。
4. `architect` 是 M6 模块 owner，负责 `sys.arch.construction-audit` 与 `system.integration.openspec-sync` 语义，以及 `construction-plane-governance` 流程治理约束；`bpm` 负责流程实例编排与关闭门禁执行。

## 规则

1. 注册前必须有完整 Agent 设计文档。
2. 生命周期采用 5 态。

## W1 联动备注（M2 BPM Runtime Hardening）

1. 本回合无新增 Agent 注册项。
2. `bpm` 设计文档已补充 `session_binding.json` 与显式 `--session-id` 调度职责。

## W2 联动备注（M2 BPM Runtime Hardening）

1. 本回合无新增 Agent 注册项与生命周期迁移。
2. `bpm/admin` 设计文档已将 `config-change-gatekeeper` 与 `system-config-updater` 状态更新为“draft（可执行）”。

## W3 联动备注（M2 BPM Runtime Hardening）

1. 本回合无新增 Agent 注册项与生命周期迁移。
2. `bpm` 设计文档已补充 trigger runtime 执行职责（`trigger-schedule-runtime` / `trigger-event-runtime` runner）与 TG 回归入口。

## W4 联动备注（M2 BPM Runtime Hardening）

1. 新增 `system-analyst` 最小可运行资产并完成注册，生命周期状态为 `review`。
2. `system-analyst` 文档已补齐 handoff 输入契约、digest/reject 输出契约、Fail-Closed 条件与最小权限边界。
3. 回归用例 `TC-ANL-001~002` 已纳入 `tests/m2-bpm-runtime/`，证据写入 `docs/design/modules/evidence/bpm-runtime/w4_system_analyst_cases/`。

## W5 联动备注（M2 BPM Runtime Hardening）

1. `system-analyst` 运行资产补齐（IDENTITY/SOUL/TOOLS/USER/MEMORY），生命周期推进到 `active`。
2. 新增生产技能 `sys.arch.system-feedback-digest`，并作为 `system-analyst` 默认执行能力。
3. 新增 `runtime-policy-calibration` 可执行流程，`TC-ANL-001~003` 完成生产路径端到端验证。
