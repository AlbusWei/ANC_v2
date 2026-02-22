# governed-config-change - Process Guide

## Purpose

将 OpenClaw 配置变更纳入 BPM 治理，确保系统级写操作由 admin 执行且全程可审计。

## Entry Conditions

1. 请求方提供 `objective_ref` 与变更目标。
2. 请求方提供最小证据链：`spec_ref`、`test_ref`、`rollback_plan`。
3. 请求方明确影响面（agent/skill/process/gateway）。

## Execution Phases

1. `p1 intake-and-normalize`（bpm）
2. `p2 gate-and-risk-classification`（bpm）
3. `p3 authorize-change`（admin）
4. `p4 execute-config-change`（admin）
5. `p5 verify-and-archive`（bpm）

## Rejection Rules (Fail-Closed)

1. 任一必填字段缺失。
2. 无法提供回滚方案。
3. 变更后健康检查失败且回滚失败。

## Primary Evidence Bundle

- `request.json`
- `gate_result.json`
- `authorization.json`
- `change_receipt.json`
- `verification_report.json`

## Runtime Tooling

1. 流程执行：
   - `python3 processes/meta/governed-config-change/scripts/governed_config_change_runner.py --input <input.json> --output <output.json>`
2. P2 门禁：
   - `python3 skills/system/config-change-gatekeeper/scripts/config_change_gatekeeper_runner.py --input <input.json> --output <output.json>`
3. P4 执行：
   - `python3 skills/system/system-config-updater/scripts/system_config_updater_runner.py --input <input.json> --output <output.json>`
