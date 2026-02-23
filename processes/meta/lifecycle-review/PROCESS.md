# lifecycle-review - Process Guide

## Purpose

将生命周期审批从文档约定升级为可执行流程，作为 `M1 -> M4` 的最小治理接点。

## Entry Conditions

1. 输入必须提供 `final_gate_verdict_ref`、`target_asset_ref`、`requested_transition`。
2. `target_asset_ref` 与 `final_gate_verdict_ref` 必须可解析。
3. 当前状态与目标状态必须满足 5 态状态机迁移规则。

## Execution Phases

1. `p1 validate-request`（hr）
2. `p2 check-prerequisites`（hr）
3. `p3 quality-gate`（hr）
4. `p4 execute-transition`（hr）
5. `p5 sync-registry`（hr）

## Rejection Rules (Fail-Closed)

1. 非法状态迁移（例如 `active -> retired` 直跳）。
2. 证据缺失或不可追溯（门禁 verdict/目标资产引用缺失）。
3. 质量门禁结果非 `pass`。
4. `registry_contract_tool.py verify` 失败。

## Primary Evidence Bundle

- `lifecycle_transition_ref`
- `registry_sync_ref`
- `lifecycle_review_report_ref`

## Runtime Tooling

1. 执行入口：
   - `python3 processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py --input <input.json> --output <output.json>`
2. registry 校验：
   - `python3 shared/registry/registry_contract_tool.py verify`
