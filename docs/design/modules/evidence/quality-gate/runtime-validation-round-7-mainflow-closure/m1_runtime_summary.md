# Runtime Validation Round 6 Summary

- 生成时间: `2026-02-22T19:01:48Z`
- 总体结果: `pass`
- 用例总数: `4`
- 通过数: `4`
- 失败数: `0`

## 判定覆盖

- pass: `True`
- fail_closed: `True`
- hold: `True`

## 用例结论

### TC-M1-CHAIN-001
- status: `pass`
- gate_decision: `pass`
- decision_class: `pass`
- evidence_index_ref: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/evidence_index.json`
- critical_refs:
  - `prep_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/prep_output.json`
  - `eval_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/eval_output.json`
  - `final_gate_verdict_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/evaluation/p4_aggregate_verdict/final_gate_verdict.json`
  - `lifecycle_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/lifecycle_output.json`
  - `lifecycle_transition_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/lifecycle/p4_lifecycle_transition.json`
  - `registry_sync_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/lifecycle/p5_registry_sync.json`
  - `lifecycle_review_report_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/lifecycle/lifecycle_review_report.json`
- notes:
  - M3->M1->M4 pass 主链路已闭环。

### TC-M1-CHAIN-002
- status: `pass`
- gate_decision: `test_invalid`
- decision_class: `fail_closed`
- evidence_index_ref: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-002/evidence_index.json`
- critical_refs:
  - `prep_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-002/prep_output.json`
  - `prep_fail_closed_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-002/preparation/fail_closed_record.json`
  - `lifecycle_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-002/lifecycle_output.json`
  - `lifecycle_fail_closed_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-002/lifecycle/fail_closed_record.json`
  - `lifecycle_transition_ref`: ``
- notes:
  - 关键输入缺失触发 test_invalid/fail-closed，且 lifecycle transition 已阻断。

### TC-M1-CHAIN-003
- status: `pass`
- gate_decision: `hold`
- decision_class: `hold`
- evidence_index_ref: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-003/evidence_index.json`
- critical_refs:
  - `prep_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-003/prep_output.json`
  - `eval_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-003/eval_output.json`
  - `hold_governance_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-003/evaluation/p5_hold_governance_output.json`
  - `hold_resolution_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-003/evaluation/p5_hold_governance/p5_hold_resolution.json`
- notes:
  - evaluation hold 已成功路由 hold-governance 并产出 hold_resolution_ref。

### TC-M1-CHAIN-004
- status: `pass`
- gate_decision: `pass`
- decision_class: `pass`
- evidence_index_ref: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-004/evidence_index.json`
- critical_refs:
  - `m5_request_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-004/m5_request.json`
  - `prep_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-004/prep_output.json`
  - `eval_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-004/eval_output.json`
  - `final_gate_verdict_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-004/evaluation/p4_aggregate_verdict/final_gate_verdict.json`
- notes:
  - M5 已最小接入 M1 门禁入口（preparation + evaluation 可执行）。

## Thread-4 联动引用

### tc_m1_chain_001_pass
- `evidence_index_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/evidence_index.json`
- `final_gate_verdict_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/evaluation/p4_aggregate_verdict/final_gate_verdict.json`
- `lifecycle_transition_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/lifecycle/p4_lifecycle_transition.json`
- `registry_sync_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-001/lifecycle/p5_registry_sync.json`

### tc_m1_chain_002_fail_closed
- `evidence_index_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-002/evidence_index.json`
- `prep_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-002/prep_output.json`
- `lifecycle_fail_closed_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-002/lifecycle/fail_closed_record.json`
- `lifecycle_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-002/lifecycle_output.json`

### tc_m1_chain_003_hold
- `evidence_index_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-003/evidence_index.json`
- `eval_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-003/eval_output.json`
- `hold_governance_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-003/evaluation/p5_hold_governance_output.json`
- `hold_resolution_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-003/evaluation/p5_hold_governance/p5_hold_resolution.json`

### tc_m1_chain_004_m5_entry
- `evidence_index_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-004/evidence_index.json`
- `m5_request_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-004/m5_request.json`
- `eval_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-004/eval_output.json`
- `final_gate_verdict_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-7-mainflow-closure/m1_chain_cases/TC-M1-CHAIN-004/evaluation/p4_aggregate_verdict/final_gate_verdict.json`

## 自然语言结论

本轮已覆盖 pass、fail-closed 与 hold 三类判定证据，并验证 M5 最小接入 M1 门禁入口可执行。
