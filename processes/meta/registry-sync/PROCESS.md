# registry-sync - Process Guide

## Purpose

将 registry 同步从散点动作收敛为治理原子流程（AP-011 包装语义），输出统一同步决策与验证证据。

## Execution Phases

1. validate-input
2. verify-registry-and-sync

## Rejection Rules (Fail-Closed)

1. patch plan 缺失或不可解析。
2. verify_scope 缺失或目标越权。
3. `registry_contract_tool.py verify` 返回非零。

## Primary Evidence Bundle

- `sync_input_snapshot.json`
- `registry_verify_report.json`
- `registry_sync_record.json`
