# escalation - Process Guide

## Purpose

将升级链路执行语义统一为可复用 P5 子流程，避免业务流程私有化升级逻辑。

## Execution Phases

1. incident-intake
2. policy-check
3. chain-routing
4. resolution-or-human

## Rejection Rules (Fail-Closed)

1. incident/evidence 缺失。
2. 升级链不完整、越级或循环。
3. policy 与上下文冲突且不可裁决。

## Primary Evidence Bundle

- `incident_snapshot.json`
- `policy_check.json`
- `escalation_trace.json`
- `escalation_output.json`
