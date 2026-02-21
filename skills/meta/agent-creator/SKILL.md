---
name: "agent-creator"
description: "Create or update agent design assets with lifecycle and registry-ready contracts"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# agent-creator

## Objective

创建或更新 Agent 资产（角色文档、工具清单、registry patch 计划），确保可治理并满足 lifecycle 门禁。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-agent-asset-authoring
input_contract:
  format: json
  required:
    - agent_id
    - role_scope
    - interfaces
    - owner
  validation:
    - agent_id must follow registry naming conventions
    - role_scope must include responsibilities and boundaries
    - interfaces must reference existing protocol docs
output_contract:
  format: file_layout_and_markdown
  required:
    - agent_doc_path
    - tools_doc_path
    - registry_patch_plan
  machine_judgement:
    - generated paths are repo-relative and reachable
    - ownership and lifecycle fields are present
    - registry patch contains required contract fields
fail_closed_rules:
  - missing mandatory identity or ownership fields
  - protocol references are missing or invalid
  - registry patch plan is incomplete
test_mount:
  test_doc: skills/meta/agent-creator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Input Contract

- Format: json
- Required fields: agent_id, role_scope, interfaces, owner

## Output Contract

- Format: file layout + markdown
- Required fields: agent_doc_path, tools_doc_path, registry_patch_plan
