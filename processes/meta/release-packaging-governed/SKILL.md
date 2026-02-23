---
name: "release-packaging-governed"
description: "P5 子流程：受治理约束的 AP-012 发布打包"
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

# release-packaging-governed

## Objective

统一发布打包输入门槛，确保 release 决策、变更日志与回滚包输出可审计。

## Input Contract

- Format: json
- Required fields: candidate_artifacts_ref, final_gate_verdict_ref, lifecycle_transition_ref, registry_sync_ref

## Output Contract

- Format: json
- Required fields: release_package_ref, changelog_ref, release_decision, rollback_bundle_ref
