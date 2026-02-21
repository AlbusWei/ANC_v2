---
name: "trigger-matcher-dedupe"
description: "Match canonical triggers and enforce idempotent dedupe ledger policies"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# trigger-matcher-dedupe

## Objective

对 canonical trigger 执行规则匹配与幂等去重，防止重复实例创建。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m2-trigger-governance-runtime
input_contract:
  format: json
  required:
    - canonical_trigger_ref
    - match_policy_ref
    - dedupe_policy_ref
  validation:
    - match policy must include target process id
    - dedupe policy must define primary key source+event_id
    - dedupe policy must define fallback key with entity and status fields plus time_bucket
    - canonical trigger fields must satisfy minimum event contract
output_contract:
  format: json
  required:
    - match_result
    - dedupe_decision
    - dedupe_key_ref
    - matcher_evidence_ref
  machine_judgement:
    - match_result is hit or miss
    - dedupe_decision is allow or reject
    - dedupe_key_ref is recorded when decision is reject
fail_closed_rules:
  - primary and fallback dedupe keys are both unavailable
  - dedupe key conflict cannot be resolved
  - target process undefined in policy
  - canonical trigger missing minimum required fields
test_mount:
  test_doc: skills/system/trigger-matcher-dedupe/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```
