---
name: "trigger-ingress-normalizer"
description: "Normalize schedule and event triggers into canonical trigger envelopes"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# trigger-ingress-normalizer

## Objective

将 `schedule|heartbeat|event|threshold` 输入统一归一为内部 canonical trigger envelope。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m2-trigger-governance-runtime
input_contract:
  format: json
  required:
    - trigger_type
    - trigger_source
    - payload_ref
    - received_at
  validation:
    - trigger_type must be schedule or heartbeat or event or threshold
    - payload_ref must be reachable
    - received_at must be RFC3339 timestamp
output_contract:
  format: json
  required:
    - canonical_trigger_ref
    - trigger_id
    - normalization_report_ref
  machine_judgement:
    - canonical trigger contains required fields
    - trigger_id is stable and unique per source event
    - normalization report is present
fail_closed_rules:
  - trigger_type is unsupported
  - required trigger payload fields missing
  - payload evidence unreachable
test_mount:
  test_doc: skills/system/trigger-ingress-normalizer/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
