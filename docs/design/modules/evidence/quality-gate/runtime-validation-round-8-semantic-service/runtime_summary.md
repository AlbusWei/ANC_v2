# Runtime Validation Round 8 - Semantic Service Summary

- 生成时间: `2026-02-22T19:18:19Z`
- 总体状态: `pass`
- gate_decision: `fail`
- qa_findings_count: `5`
- qa_debug_steps_count: `5`

## 关键证据

- `service_request_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-8-semantic-service/TC-M1-SERVICE-001/service_request.md`
- `process_instance_start_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-8-semantic-service/TC-M1-SERVICE-001/process_instance_start.json`
- `qa_design_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-8-semantic-service/TC-M1-SERVICE-001/qa_design_payload.json`
- `test_doc_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-8-semantic-service/TC-M1-SERVICE-001/TEST_service_llm.md`
- `preparation_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-8-semantic-service/TC-M1-SERVICE-001/prep_output.json`
- `evaluation_output_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-8-semantic-service/TC-M1-SERVICE-001/evaluation/raw_eval.json`
- `raw_eval_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-8-semantic-service/TC-M1-SERVICE-001/evaluation/raw_eval.json`
- `qa_execution_report_ref`: `docs/design/modules/evidence/quality-gate/runtime-validation-round-8-semantic-service/TC-M1-SERVICE-001/qa_execution_report.json`

## 自然语言结论

已完成真实服务场景验证：QA agent 先产出测试设计，再对 mock 交付进行 LLM 语义评审，门禁阻断并输出可执行 debug 建议。
