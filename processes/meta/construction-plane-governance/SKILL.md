---
name: "construction-plane-governance"
description: "Govern M6 construction-plane update rounds with linkage audit, OpenSpec sync and fail-closed verification"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.2.0"
---

# construction-plane-governance

## Objective

为 M6 提供统一施工治理流程，确保每次模块级变更都完成联动落盘、OpenSpec 双向同步与门禁校验。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: bpm, architect, admin
- Priority support: P0 / P1

## Input Contract

- Format: json
- Required fields: round_id, round_goal, change_scope_ref, changed_assets, linkage_targets, owner, openspec_ref

## Output Contract

- Format: json
- Required fields: m6_update_bundle_ref, linkage_report_ref, registry_verify_report_ref, construction_plane_delta_ref, open_questions_ref, openspec_sync_ref, round_evidence_log_ref, round_close_summary_ref

## Runtime Rules

1. 任何模块边界变更必须触发联动审计。
2. OpenSpec 同步必须由 `system.integration.openspec-sync` 产出结构化记录。
3. registry 校验失败时不得关闭回合。
4. 开放问题必须带 owner 与下一步。
5. 架构相关变更必须完成 OpenSpec 双向同步并附裁决快照。
6. phase/AP 映射固定为 AP-032~AP-036，禁止使用未定义 phase 映射。
