---
name: "software-vendor-e2e-flow"
description: "P4 外部软件交付主线，强制在 delivery-iterations 复用 full-development canonical"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.1.0"
---

# software-vendor-e2e-flow

## Objective

将外部软件交付主线收敛为可执行流程，并通过 `delivery-iterations` 强制复用内部 canonical `full-development`，避免出现旁路交付。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: architect, bpm
- Priority support: P1

## Input Contract

- Format: json
- Required fields: `lead_context_ref`, `customer_constraints_ref`, `lifecycle_target`

## Output Contract

- Format: json
- Required fields: `final_gate_verdict_ref`, `lifecycle_transition_ref`, `registry_sync_ref`, `release_package_ref`, `customer_acceptance_ref`, `support_feedback_ref`

## Fail-Closed 决策

1. `delivery-iterations` 未复用 `full-development`：返回 `2`。
2. 外部主线缺失关键门禁链路（`quality-gate-preparation/evaluation/lifecycle-review/registry-sync`）：返回 `2`。
3. 生命周期请求超过 `review`：返回 `2`。
4. 运行异常：返回 `1`。

## 运行命令

```bash
# 启动外部主线 p1（在线分发）
python3 skills/system/process-instance-manager/scripts/process_instance_runner.py start \
  --process-id software-vendor-e2e-flow \
  --phase-id p1 \
  --instance-root tmp/session6/process_instances \
  --initiated-by bpm \
  --input-ref tmp/session6/lead_context.md \
  --dispatch-message "Session6 外部主线 lead-intake" \
  --openclaw-bin openclaw \
  --openclaw-stall-threshold-seconds 900 \
  --execute-openclaw \
  --reset-openclaw-session \
  --strict-session-match \
  --output tmp/session6/software_vendor_p1_dispatch.json

# Session6 全量外部主线套件
python3 tests/m3-self-development/session6_external_runner.py \
  --evidence-root tmp/runtime_data/execution/evidence/construction-plane/R-20260222-M6-m3-self-development-e2e-online-01/session6 \
  --report session6_report.json
```

## 返回码语义

1. `0`：通过（外部主线用例全通过）。
2. `2`：Fail-Closed（旁路、证据缺失、生命周期越级等）。
3. `1`：运行异常。
