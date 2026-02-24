---
name: "evidence-archiver"
description: "Archive quality gate evidence into indexed packages with traceability links for M1 M2 and M4 consumers"
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

# evidence-archiver

## Objective

将评测产物归档为统一证据包，生成 `index.json` 与可追溯链接，供 M2/M4 消费。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: cli
  required:
    - run_id
    - profile_id
    - gate_decision
    - actor
    - output_dir
  validation:
    - gate_decision must be pass or fail or hold or test_invalid
    - input refs and reasons must be serializable
output_contract:
  format: file_layout_and_json
  required:
    - evidence_ref
    - evidence_index_ref
    - archive_report_ref
    - gate_decision
    - reasons
  machine_judgement:
    - evidence index includes required traceability fields
    - unified_verdict.json exists
    - archive report is traceable
fail_closed_rules:
  - invalid gate_decision must fail
  - missing required metadata must fail
  - evidence package write failure must fail
test_mount:
  test_doc: skills/system/qa/evidence-archiver/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  index_schema: skills/system/qa/evidence-archiver/references/evidence-index.md
  script: skills/system/qa/evidence-archiver/scripts/archive_evidence.py
```

## Input Contract

- Format: CLI
- Required fields:
  - `--run-id`
  - `--profile-id`
  - `--gate-decision`
  - `--actor`
  - `--output-dir`

## Output Contract

- Format: file layout + json
- Required fields:
  - `evidence_ref`
  - `evidence_index_ref`
  - `archive_report_ref`
  - `gate_decision`
  - `reasons[]`

## Execution Steps

1. 校验门禁结论与元数据。
2. 校验 `input_refs/raw_eval_ref` 可达性并生成 traceability manifest（含 hash）。
3. 生成证据目录与 `index.json`。
4. 写入 `unified_verdict.json` 与归档报告。
5. 输出可追溯引用。

最小执行命令：

```bash
python3 skills/system/qa/evidence-archiver/scripts/archive_evidence.py \
  --run-id smoke-001 \
  --profile-id quality-gate.baseline@1.0.0 \
  --gate-decision pass \
  --actor qa \
  --reason smoke_pass \
  --output-dir runtime_data/execution/evidence/quality-gate/smoke/evidence-archiver
```

## Fail-Closed Rules

- `gate_decision` 枚举非法时 `fail`。
- 缺失 `run_id/profile_id/actor` 时 `fail`。
- 证据写入失败时 `fail`。

## References

- 证据索引字段：`skills/system/qa/evidence-archiver/references/evidence-index.md`
