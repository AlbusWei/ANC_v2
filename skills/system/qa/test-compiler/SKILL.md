---
name: "test-compiler"
description: "Compile TEST.md into executable datapoints and deterministic tc_id/profile bindings for M1 quality gate preparation"
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

# test-compiler

## Objective

将 `TEST.md` 编译为可执行 datapoints，输出 `tc_id -> profile_id` 映射、评测配置与编译证据。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: json_or_cli
  required:
    - test_doc_ref
    - objective_ref
    - spec_ref
    - profile_set
  validation:
    - test_doc_ref must point to a reachable TEST.md
    - objective_ref and spec_ref must be resolvable
    - profile_set must include baseline profile
output_contract:
  format: json
  required:
    - test_datapoints_ref
    - tc_profile_map_ref
    - compile_report_ref
    - gate_decision
    - evidence_ref
    - reasons
  machine_judgement:
    - output is valid json
    - tc_profile_map_ref contains one-to-one tc_id to profile_id mapping
    - compile_report_ref records compile summary and failures
fail_closed_rules:
  - TEST.md parse failure must return test_invalid
  - missing P0 test datapoints must fail
  - missing tc_id to profile_id mapping must fail
test_mount:
  test_doc: skills/system/qa/test-compiler/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  output_schema: skills/system/qa/test-compiler/references/output-schema.md
  script: skills/system/qa/test-compiler/scripts/compile_test_doc.py
```

## Input Contract

- Format: json or CLI args
- Required fields:
  - `test_doc_ref`
  - `objective_ref`
  - `spec_ref`
  - `profile_set`

## Output Contract

- Format: json
- Required fields:
  - `test_datapoints_ref`
  - `tc_profile_map_ref`
  - `compile_report_ref`
  - `gate_decision`
  - `evidence_ref`
  - `reasons[]`

## Execution Steps

1. 校验输入路径与 profile 集合。
2. 解析 `TEST.md`，提取 `TC-*`、`Priority`、`Evaluation Method`、`Judge Payload`、`Evaluation Configuration`。
3. 生成 datapoints 与 `tc_id -> profile_id` 映射。
4. 写入 `compile_report_ref` 并输出统一 verdict 字段。
5. 任何关键校验失败立即 Fail-Closed。

最小执行命令：

```bash
python3 skills/system/qa/test-compiler/scripts/compile_test_doc.py \
  --test-doc skills/system/qa/test-compiler/TEST.md \
  --objective-ref obj-m1-unified-quality-gate \
  --spec-ref docs/design/modules/M1-openjudge-adapter-spec.md \
  --profile-set quality-gate.baseline@1.0.0 \
  --output-dir runtime_data/execution/evidence/quality-gate/smoke/test-compiler
```

## Fail-Closed Rules

- 无法解析 `TEST.md` 时返回 `gate_decision=test_invalid`。
- 缺失 P0 用例时返回 `gate_decision=fail`。
- 无法生成映射或证据路径时返回 `gate_decision=fail`。

## References

- 输出契约说明：`skills/system/qa/test-compiler/references/output-schema.md`
