---
name: "evidence-recorder"
description: "Record trigger runtime evidence index and enforce traceability constraints"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# evidence-recorder

## Objective

统一记录触发命中、拒绝、补跑、升级等证据条目，保证触发与实例双向追溯。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m2-trigger-governance-runtime
input_contract:
  format: json
  required:
    - trigger_id
    - instance_id
    - decision
    - evidence_payload_ref
  validation:
    - decision must be hit or reject or catchup or escalate
    - trigger_id must be stable
    - evidence payload must include actor and timestamp
output_contract:
  format: json
  required:
    - trigger_receipt_ref
    - evidence_index_ref
    - traceability_link_ref
  machine_judgement:
    - evidence index includes trigger_id and instance_id
    - traceability link can resolve both directions
    - trigger receipt contains final decision
fail_closed_rules:
  - missing trigger_id or instance_id
  - evidence payload missing actor or timestamp
  - traceability link generation failed
test_mount:
  test_doc: skills/system/evidence-recorder/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Runtime Entrypoint

1. 可执行入口：`skills/system/evidence-recorder/scripts/evidence_recorder_runner.py`
2. 最小命令：
   - `python3 skills/system/evidence-recorder/scripts/evidence_recorder_runner.py --input <input.json> --output <output.json> --receipt <trigger_receipt.json> --index <evidence_index.jsonl> --trace <traceability.json>`
