---
name: "construction-audit"
description: "Audit M6 construction-plane linkage completeness across design docs, inventories, registries and construction board"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# construction-audit

## Objective

审计单次建设回合是否满足 `M6` 联动门禁，输出可执行缺口清单与阻断项。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m6-construction-plane-governance
input_contract:
  format: json
  required:
    - change_scope_ref
    - changed_assets
    - linkage_targets
    - round_goal
    - openspec_ref
  validation:
    - change_scope_ref must point to a reachable planning or requirement document
    - changed_assets must be a non-empty list of repo-relative paths
    - linkage_targets must include docs, inventory and registry scopes
    - round_goal must be explicit and testable
    - openspec_ref must be provided for architecture-affecting changes
output_contract:
  format: json
  required:
    - linkage_report_ref
    - missing_items
    - blocking_risks
    - recommended_actions
    - openspec_sync_ref
  machine_judgement:
    - linkage_report_ref is present and reachable
    - missing_items and blocking_risks are arrays
    - recommended_actions is non-empty when missing_items is non-empty
fail_closed_rules:
  - missing required input fields
  - linkage_targets does not include registry checks
  - missing openspec_ref for architecture-affecting rounds
  - openspec and ANC design semantics conflict without architect decision snapshot
  - unresolved blocking risks without owner assignment
  - unreachable evidence references
test_mount:
  test_doc: skills/system/construction-audit/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  module_spec: docs/design/modules/M6-construction-plane.md
  process_spec: docs/design/processes/construction-plane-governance-process.md
  openspec_protocol: docs/design/interfaces/openspec-collaboration-protocol.md
```
