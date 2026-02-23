---
name: "system-feedback-digest"
description: "Validate system-analysis handoff and produce auditable structured digest or fail-closed rejection"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# system-feedback-digest

## Objective

承接 `system-analyst` 的 handoff 输入，输出结构化 digest；证据不足时输出可审计拒绝记录。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-runtime-policy-calibration
input_contract:
  format: json
  required:
    - handoff_ref
  validation:
    - handoff_ref must be reachable
    - handoff must include role-handoff required fields
    - handoff.to_role must equal system-analyst
    - handoff.evidence_ref must be reachable and non-empty
output_contract:
  format: json
  required:
    - status
    - architecture_feedback_digest_ref_or_reject_ref
    - generated_at
  machine_judgement:
    - status completed means digest ref exists and is reachable
    - status rejected means reject ref exists and includes reason_code
    - all outputs include instance_id and auditable trace
fail_closed_rules:
  - missing handoff fields
  - evidence index unreachable or empty
  - objective_ref path not reachable in repo
  - lineage metadata invalid
test_mount:
  test_doc: skills/system/system-feedback-digest/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Runtime Entrypoint

1. 可执行入口：`skills/system/system-feedback-digest/scripts/system_feedback_digest_runner.py`
2. 最小命令：
   - `python3 skills/system/system-feedback-digest/scripts/system_feedback_digest_runner.py --input <input.json> --output <output.json>`
