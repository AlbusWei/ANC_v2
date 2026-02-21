# construction-plane-governance - Process Guide

## Purpose

将施工面维护标准化为可执行流程，避免“模块落盘完成但联动资产缺失”的倒挂。

## Entry Conditions

1. 已定义本回合 `round_id` 与 `round_goal`。
2. 已提交 `changed_assets` 与影响范围。
3. 已声明需同步的 `linkage_targets`（docs/inventory/registry/construction_plane）。
4. 架构相关变更提供 `openspec_ref`。

## Execution Phases

1. `p1 scope-intake-and-baseline`（bpm / `system.ops.manual-task`）
2. `p2 run-construction-audit`（architect / `sys.arch.construction-audit`）
3. `p3 execute-linked-updates`（architect / `system.ops.manual-task`）
4. `p4 sync-openspec-state`（architect / `system.integration.openspec-sync`）
5. `p5 verify-and-close`（bpm / `system.ops.manual-task`）

## Rejection Rules (Fail-Closed)

1. 受影响清单不完整。
2. 审计阻断项未清零。
3. registry 合约校验失败。
4. OpenSpec 双向映射缺失或语义冲突未裁决。
5. 回合日志缺失 round_close 事件或 checkpoint/commit 对账失败。

## Primary Evidence Bundle

- `scope_baseline.md`
- `linkage_report.md`
- `update_delta.md`
- `registry_verify.log`
- `construction_plane_delta.md`
- `openspec_sync_report.md`
- `round-evidence.jsonl`
- `round-close-summary.md`
