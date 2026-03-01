---
name: "process-instance-manager"
description: "Manage BPM process instance lifecycle with canonical phase dispatch context and strict lineage isolation"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.4.0"
---

# process-instance-manager

## Objective

统一管理流程实例创建、phase 任务分发、上下文拼接与 lineage 隔离，确保多 agent 多会话协作可执行、可追溯。

同时内含三类核心子能力：manifest 解析、phase 分发协议组装、lineage 守卫。

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
    - phase dispatch context must include purpose + done_definition + handoff_note
    - phase input refs are composed by explicit refs -> parent output -> spec_ref
    - lineage_ref must be present for recursive invocation
    - stack_depth must be less than lineage policy limit
    - session_binding.session_id must not reuse parent_session_id
output_contract:
  format: json
  required:
    - instance_id
    - runtime_state
    - state_transition_ref
    - task_dispatch_ref
    - dispatch_context_ref
    - evidence_ref
  machine_judgement:
    - instance_id is generated and stable
    - runtime_state is in running or hold or fail or complete
    - state_transition_ref/task_dispatch_ref/dispatch_context_ref are present
    - schedule and lineage checks are recorded in evidence
    - manifest phase target mapping follows subprocess + inline_ap canonical rules
fail_closed_rules:
  - missing process or phase contract
  - process manifest parse failure or phase closure violation
  - mutable context leak between parent and child
  - stack_depth exceeds configured limit
  - missing session_binding or explicit session_id
  - child session reuses parent session
  - missing state transition evidence
  - invalid subprocess target binding (missing inline_ap or unresolved skill_id)
  - phase dispatch context cannot be composed (missing semantic fields)
test_mount:
  test_doc: skills/system/process-instance-manager/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Executable Runner

`skills/system/process-instance-manager/scripts/process_instance_runner.py`

执行规则（对齐 `docs/architecture/process_architecture.md`）：

1. 读取 `process.json` 并校验 canonical 约束（`subprocess + inline_ap + spec_ref`）。
2. 计算 lineage 与 session 绑定，禁止子实例复用父会话。
3. 组装 phase 分发上下文：`phase_purpose/input_context_ref/done_definition/handoff_note`。
4. 按优先级拼接 phase 输入：显式 `input_ref` -> 父实例最近输出 -> `spec_ref`。
5. 生成并落盘 `task_dispatch.json`（BPM canonical dispatch 包）与 `dispatch_context.json`。
6. 生成自然语言 `dispatch_prompt.md`，把目标、输入、完成标准和交接要求传给 Actor。
7. 真实分发时显式传 `--session-id` 调 OpenClaw，并记录回执与活性探测证据。

会话治理参数：

1. `--reset-openclaw-session`：分发前执行 `sessions.reset`，为同 actor 新建会话上下文。
2. `--strict-session-match`：校验实际 OpenClaw 会话 ID 与上下文会话 ID 一致。
3. `--openclaw-stall-threshold-seconds`：停滞判定阈值（最小 900 秒），仅在“输出增量 + 会话活性”均长期无进展时触发停滞终止。
4. `--openclaw-probe-interval-seconds`：活性探测轮询间隔（默认 60 秒）。
5. `--openclaw-timeout-seconds`：保留兼容别名，语义已切换为停滞阈值，不再作为硬超时。
