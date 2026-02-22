---
name: "registry-validator"
description: "Validate ANC registry contracts and emit structured pass or fail evidence for lifecycle gates"
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

# registry-validator

## Objective

封装 registry 合约校验，输出结构化验证报告，供 lifecycle-review 与发布门禁复用。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m1-unified-quality-gate
input_contract:
  format: cli
  required:
    - registry_tool_ref
    - verify_scope
    - output_dir
  validation:
    - registry_tool_ref must be executable
    - verify_scope must include skill_registry at minimum
output_contract:
  format: json
  required:
    - validation_report_ref
    - gate_decision
    - evidence_ref
    - reasons
  machine_judgement:
    - gate_decision is pass or fail
    - validation_report_ref is traceable
    - raw verify output is preserved
fail_closed_rules:
  - verify command non-zero must fail
  - malformed report payload must fail
  - missing evidence output must fail
test_mount:
  test_doc: skills/system/qa/registry-validator/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
references:
  registry_contract: skills/system/qa/registry-validator/references/registry-contract.md
  script: skills/system/qa/registry-validator/scripts/validate_registry.py
```

## Input Contract

- Format: CLI
- Required fields:
  - `--registry-tool`
  - `--verify-scope`
  - `--output-dir`

## Output Contract

- Format: json
- Required fields:
  - `validation_report_ref`
  - `gate_decision`
  - `evidence_ref`
  - `reasons[]`

## Execution Steps

1. 调用 `registry_contract_tool.py verify`。
2. 收集 stdout/stderr/return code。
3. 写入结构化验证报告。
4. 失败时立即 Fail-Closed 并输出证据路径。

最小执行命令：

```bash
python3 skills/system/qa/registry-validator/scripts/validate_registry.py \
  --registry-tool shared/registry/registry_contract_tool.py \
  --verify-scope skill_registry \
  --output-dir docs/design/modules/evidence/quality-gate/smoke/registry-validator
```

## Fail-Closed Rules

- verify 失败返回 `gate_decision=fail`。
- 报告结构不可解析返回 `gate_decision=fail`。
- 证据写入失败返回 `gate_decision=fail`。

## References

- registry contract 协议：`skills/system/qa/registry-validator/references/registry-contract.md`
