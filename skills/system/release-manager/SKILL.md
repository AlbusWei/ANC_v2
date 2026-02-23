---
name: "release-manager"
description: "Assemble release package, changelog and rollback bundle with strict lifecycle and registry gates"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# release-manager

## Objective

在发布阶段统一执行发布包组装、变更日志生成、发布决策与回滚包可用性校验，缺少关键门禁证据时 Fail-Closed。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-release-governance
input_contract:
  format: json
  required:
    - candidate_artifacts_ref
    - final_gate_verdict_ref
    - lifecycle_transition_ref
    - registry_sync_ref
  validation:
    - candidate_artifacts_ref must be reachable and include release candidates
    - final_gate_verdict_ref must be reachable and gate decision must be pass
    - lifecycle_transition_ref must be reachable
    - registry_sync_ref must be reachable
output_contract:
  format: json
  required:
    - release_package_ref
    - changelog_ref
    - release_decision
    - rollback_bundle_ref
  machine_judgement:
    - release_decision in [approved, rejected, blocked]
    - release_package_ref and changelog_ref must be reachable when approved
    - rollback_bundle_ref must be reachable when approved
fail_closed_rules:
  - reject when prerequisite gate evidence is missing
  - block when registry sync verification fails
  - reject when rollback bundle is unavailable
test_mount:
  test_doc: skills/system/release-manager/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Runtime Entrypoint

1. 可执行入口：`skills/system/release-manager/scripts/release_manager_runner.py`
2. 最小命令：
   - `python3 skills/system/release-manager/scripts/release_manager_runner.py --input <input.json> --output <output.json>`
