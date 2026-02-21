# hold-governance - Process Guide

## Purpose

在 `hold` 情况下通过标准化 triage 与运行治理保持系统可恢复性和可追溯性。

## Entry Conditions

1. 评测流程产出 hold。
2. hold case 引用和运行日志可访问。
3. triage 与健康策略可解析。

## Execution Phases

1. `p1 collect-progress-evidence`（qa / `sys.qa.hold-triage`）
2. `p2 triage-and-classify`（qa / `sys.qa.hold-triage`）
3. `p3 execute-triage-action`（qa / `sys.qa.hold-triage`）
4. `p4 health-maintenance`（bpm / `sys.bpm.process-instance-manager`）
5. `p5 close-or-escalate`（bpm / `sys.bpm.escalation-handler`）

## Rejection Rules (Fail-Closed)

1. 关键进展信号缺失且无法补证。
2. triage 无明确决策。
3. 升级链不完整或证据不可追溯。

## Primary Evidence Bundle

- `progress_evidence_ref`
- `triage_report_ref`
- `action_execution_ref`
- `health_maintenance_ref`
- `hold_resolution_ref`
