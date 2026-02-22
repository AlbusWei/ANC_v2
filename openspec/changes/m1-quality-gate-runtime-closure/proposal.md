## Why

M1 质量门禁运行收口需要一个线程化、可审计、可对账的执行基座。当前工作优先完成 Thread-0 基座初始化，把 Thread-1~5 的目标、依赖与验收标准固化，避免后续线程各自解释范围导致偏航。

同时，本变更明确继承 M2 已完成成果（QA 三流程 `review`、`runtime-policy-calibration` `review`、`system-analyst` `review`、`verify-m2` 已存在），不重复建设已完成事项。

## What Changes

- 初始化 OpenSpec change：`m1-quality-gate-runtime-closure`。
- 新增 `thread-plan.md`，作为 Thread-0~5 的唯一对齐源，统一：
  - `round_id`: `R-20260222-M6-m1-quality-gate-runtime-closure-01`
  - `openspec_ref`: `m1-quality-gate-runtime-closure`
- 更新三件套：`proposal.md`、`design.md`、`tasks.md`，按 Thread-0~5 定义依赖关系与 DoD。
- 初始化本轮 M6 证据目录，写入 `round_open` 事件和线程交接基线。

## Capabilities

### New Capabilities

- `m1-quality-gate-runtime-closure-thread-baseline`: 为 M1 运行收口提供线程化计划、交接协议和 Entire/commit 最小执行策略。

### Modified Capabilities

- `construction-plane`: 新增本轮 evidence 目录与 `round_open` 记录，确保后续线程有统一回合上下文。

## Impact

- Affected OpenSpec assets:
  - `openspec/changes/m1-quality-gate-runtime-closure/thread-plan.md`
  - `openspec/changes/m1-quality-gate-runtime-closure/proposal.md`
  - `openspec/changes/m1-quality-gate-runtime-closure/design.md`
  - `openspec/changes/m1-quality-gate-runtime-closure/tasks.md`
- Affected M6 evidence assets:
  - `docs/design/modules/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/*`
- Explicitly not included in Thread-0:
  - 不实施 Thread-1~5 的功能改造。
  - 不重复执行已由 M2 完成的注册、review 推进与 `verify-m2` 基础能力建设。

