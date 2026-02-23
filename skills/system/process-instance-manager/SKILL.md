---
name: "process-instance-manager"
description: "Manage BPM process instance lifecycle with strict lineage isolation"
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

# process-instance-manager

## Objective

统一管理流程实例创建、状态推进、上下文隔离与回填，确保父子实例不共享可变上下文。

同时内含三个子能力：manifest 解析、phase 调度、lineage 守卫。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m2-bpm-runtime-core
input_contract:
  format: json
  required:
    - process_id
    - phase_id
    - instance_context_ref
    - session_binding
    - lineage_ref
    - stack_depth
    - process_version
    - process_level
  validation:
    - process_id must exist in process_registry
    - phase_id must belong to target process
    - process manifest must be parseable and phase-closed
    - lineage_ref must be present for recursive invocation
    - stack_depth must be less than lineage policy limit
    - session_binding.session_id must not reuse parent_session_id
output_contract:
  format: json
  required:
    - instance_id
    - runtime_state
    - state_transition_ref
    - evidence_ref
  machine_judgement:
    - instance_id is generated and stable
    - runtime_state is in running or hold or fail or complete
    - state_transition_ref and evidence_ref are present
    - schedule and lineage checks are recorded in evidence
fail_closed_rules:
  - missing process or phase contract
  - process manifest parse failure or phase closure violation
  - mutable context leak between parent and child
  - stack_depth exceeds configured limit
  - missing session_binding or explicit session_id
  - child session reuses parent session
  - missing state transition evidence
test_mount:
  test_doc: skills/system/process-instance-manager/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Executable Runner

`skills/system/process-instance-manager/scripts/process_instance_runner.py`

新增会话治理参数（v0.2.0）：

1. `--reset-openclaw-session`：分发前执行 `sessions.reset`，为同 actor 新建会话上下文。
2. `--strict-session-match`：校验实际 OpenClaw 会话 ID 与上下文会话 ID 一致。
