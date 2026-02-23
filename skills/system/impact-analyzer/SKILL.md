---
name: "impact-analyzer"
description: "Analyze change impact scope, rollback requirements and gating recommendation with fail-closed controls"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
---

# impact-analyzer

## Objective

在元层与流程层变更前执行影响面分析与回滚要求评估，输出可审计门禁建议；证据不足或约束冲突时 Fail-Closed。

## Capability Contract (Machine-Readable)

```yaml
contract_version: 1.0.0
objective_ref: obj-m3-impact-analysis
input_contract:
  format: json
  required:
    - change_proposal_ref
    - affected_scope_ref
    - risk_constraints_ref
  validation:
    - change_proposal_ref must be reachable and parseable
    - affected_scope_ref must be reachable and include non-empty affected assets
    - risk_constraints_ref must be reachable and parseable
output_contract:
  format: json
  required:
    - impact_report_ref
    - risk_level
    - rollback_requirements
    - gating_recommendation
  machine_judgement:
    - risk_level in [low, medium, high, critical]
    - gating_recommendation in [allow, hold, reject]
    - impact_report_ref must be reachable
fail_closed_rules:
  - reject when change proposal is not parseable
  - hold when affected scope evidence is unreachable or empty
  - reject when risk constraints conflict without adjudication
test_mount:
  test_doc: skills/system/impact-analyzer/TEST.md
  methodology_ref: docs/architecture/test_methodology.md
```

## Runtime Entrypoint

1. 可执行入口：`skills/system/impact-analyzer/scripts/impact_analyzer_runner.py`
2. 最小命令：
   - `python3 skills/system/impact-analyzer/scripts/impact_analyzer_runner.py --input <input.json> --output <output.json>`
