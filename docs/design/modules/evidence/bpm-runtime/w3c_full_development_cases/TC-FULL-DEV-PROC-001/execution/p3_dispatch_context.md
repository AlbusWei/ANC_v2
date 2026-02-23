# p3 协作上下文
- actor: qa
- target: subprocess:quality-gate-preparation
- purpose: 围绕规格构建测试准备包，明确后续验证基线。
- input_refs: docs/design/modules/evidence/bpm-runtime/w3c_full_development_cases/TC-FULL-DEV-PROC-001/execution/p2_outputs/spec_ref.json
- done_definition: 必须产出 test_plan_ref 与 preparation_bundle_ref。
- handoff_note: 将 test_plan_ref 与 preparation_bundle_ref 交接给 p4。
