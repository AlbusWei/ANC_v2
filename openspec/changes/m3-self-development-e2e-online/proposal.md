## Why

当前 M3 已有模块与流程设计资产，但关键验收项未闭合，`full-development/hotfix/refactor` 三条主流程仍处于 `draft` 且与 `development-loop-core-standard` 在 phase 执行语法与治理绑定上存在闭合差距。同时，`sys.arch.impact-analyzer`、`sys.admin.release-manager`、`registry-sync`、`escalation`、`release-manager-agent` 等设计中资产尚未落地，导致 M3 无法进入内部/外部双主线 E2E 的可靠准入。

本回合先完成 Session1 基座：仅做设计闭合差距审计与 OpenSpec/M6 运行基线初始化，不做功能开发；生命周期目标收敛到 `review`，不推进 `active`。

## What Changes

- 启动 `m3-self-development-e2e-online` change，并补齐 Session1 所需治理文档：`proposal/design/tasks/thread-plan/m3-gap-baseline`。
- 新增 OpenSpec delta specs（含 Scenario），将“设计闭合、资产落地、会话依赖、review 收敛”固化为可验证要求。
- 初始化 M6 证据目录 `R-20260222-M6-m3-self-development-e2e-online-01`，落盘 `scope_baseline/open_questions/thread_handoff/round-evidence`。
- 在施工平面新增 `m3-self-development-e2e-online` 的 Session2~Session7 依赖顺序与逐项 DoD（非泛化、可执行口径）。
- 明确 Session1 边界：禁止实现型改造，仅输出审计基线与后续会话执行契约。

## Capabilities

### New Capabilities
- `m3-self-development-e2e-online-foundation`: 定义 M3 设计闭合差距矩阵、缺失资产落地路径、会话依赖与 lifecycle 上限（review）的基线要求。

### Modified Capabilities
- `construction-plane`: 增补 `m3-self-development-e2e-online` Session2~Session7 的依赖链、DoD 与 M6 round_open 基线要求。

## Impact

- Affected docs:
  - `openspec/changes/m3-self-development-e2e-online/*`
  - `openspec/changes/m3-self-development-e2e-online/specs/**/spec.md`
  - `docs/architecture/construction_plane.md`
  - `docs/design/modules/evidence/construction-plane/R-20260222-M6-m3-self-development-e2e-online-01/*`
- Affected governance:
  - Session1 仅建立“设计闭合 + 资产落地”执行契约，不触发功能实现。
- Affected lifecycle:
  - 本回合生命周期上限固定为 `review`，禁止推进 `active`。
