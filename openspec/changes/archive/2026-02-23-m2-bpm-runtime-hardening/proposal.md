## Why

M2 的 BPM runtime hardening 需要先建立可审计、可按回合追溯的执行基座，否则后续线程提交与实盘回归将无法对账。当前变更先落治理骨架与证据链，避免在证据不足时推进实现。

## What Changes

- 建立 `m2-bpm-runtime-hardening` 的 OpenSpec 变更骨架并推进到 apply-ready。
- 初始化并收口测试入口与回归执行器（`tests/m2-bpm-runtime/TEST.md`、`tests/m2-bpm-runtime/run_post_dev_regression.py`、`tests/m2-bpm-runtime/run_tc_online.py`）。
- 初始化证据目录及文件（含 `checkpoint_commit_map.jsonl`、`git_range.txt`、`m6_live_regression_plan.md`）。
- 在施工平面完成状态收口并关闭 `Q-001`（前置条件：`verify/verify-m2/verify-m6` + live regression 全通过）。
- 建立 checkpoint 与 commit 的映射落盘机制，供 Thread 1~6 对账使用。

## Capabilities

### New Capabilities
- `bpm-runtime-hardening-audit-foundation`: Define auditable scaffolding, checkpoint/commit mapping records, and M6 live-regression pre-embedded evidence for M2 execution rounds.

### Modified Capabilities
- `construction-plane`: Update execution status tracking from In Progress to closed-out and mark `Q-001` as Closed after gate pass.

## Impact

- Affected docs: `docs/architecture/construction_plane.md`, `docs/design/modules/evidence/bpm-runtime/*`.
- Affected test harness: `tests/m2-bpm-runtime/*`（新增 online test case 与 live regression 实执行）。
- Affected process auditability: Entire checkpoint linkage and OpenSpec apply-readiness evidence.
