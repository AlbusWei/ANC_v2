---
name: "hold-triage"
description: "Collect hold progress signals and output governed triage actions continue, retry, debug, or fail"
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

# hold-triage

## Objective

在 HOLD 场景中执行证据采集、triage 分类与动作执行，避免用固定超时直接判失败。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: json_or_cli
  required:
    - hold_case_ref
    - runtime_log_ref
    - execution_state_ref
    - triage_policy_ref
  validation:
    - hold_case_ref must be resolvable
    - progress signals must include log delta, phase progress, and output heartbeat
    - triage_policy_ref must define continue/retry/debug/fail
output_contract:
  format: json
  required:
    - progress_signals_ref
    - triage_action
    - triage_report_ref
    - action_execution_ref
    - gate_decision
    - evidence_ref
    - reasons
  machine_judgement:
    - triage_action is continue or retry or debug or fail
    - triage_report_ref is traceable
    - action_execution_ref matches selected action
fail_closed_rules:
  - missing progress signals and unable to recover evidence must fail
  - triage decision absent must fail
  - evidence chain untraceable must fail
test_mount:
  test_doc: skills/system/qa/hold-triage/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  triage_signals: skills/system/qa/hold-triage/references/triage-signals.md
  script: skills/system/qa/hold-triage/scripts/hold_triage.py
```

## Input Contract

- Format: json or CLI
- Required fields:
  - `hold_case_ref`
  - `runtime_log_ref`
  - `execution_state_ref`
  - `triage_policy_ref`

## Output Contract

- Format: json
- Required fields:
  - `progress_signals_ref`
  - `triage_action`
  - `triage_report_ref`
  - `action_execution_ref`
  - `gate_decision`
  - `evidence_ref`
  - `reasons[]`

## Execution Steps

1. 读取 hold 案例、运行日志与状态快照。
2. 计算三类进展信号：日志增量、阶段推进、输出心跳。
   - 支持对比 `previous-runtime-log` 与 `previous-execution-state` 做增量判断。
   - 心跳可由布尔标记或时间戳 + policy(`heartbeat_max_age_seconds`) 推导。
3. 按 triage policy 产出动作：`continue|retry|debug|fail`。
4. 写入 triage report、action execution 与统一 verdict。

最小执行命令：

```bash
python3 skills/system/qa/hold-triage/scripts/hold_triage.py \
  --hold-case runtime_data/execution/evidence/quality-gate/smoke/hold_case.json \
  --runtime-log runtime_data/execution/evidence/quality-gate/smoke/runtime.log \
  --execution-state runtime_data/execution/evidence/quality-gate/smoke/execution_state.json \
  --triage-policy runtime_data/execution/evidence/quality-gate/smoke/triage_policy.json \
  --output-dir runtime_data/execution/evidence/quality-gate/smoke/hold-triage
```

## Fail-Closed Rules

- 三类进展信号均缺失时 `gate_decision=fail`。
- triage_action 不在允许枚举时 `gate_decision=fail`。
- 关键证据写入失败时 `gate_decision=fail`。

## References

- triage 信号定义：`skills/system/qa/hold-triage/references/triage-signals.md`
