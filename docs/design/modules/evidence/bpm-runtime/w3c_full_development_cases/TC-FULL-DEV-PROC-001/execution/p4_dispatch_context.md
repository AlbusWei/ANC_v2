# p4 协作上下文
- actor: kernel-dev
- target: subprocess:implementation-execution-core
- purpose: 在规格与测试基线约束下完成实现与候选产物。
- input_refs: docs/design/modules/evidence/bpm-runtime/w3c_full_development_cases/TC-FULL-DEV-PROC-001/execution/p2_outputs/spec_ref.json,docs/design/modules/evidence/bpm-runtime/w3c_full_development_cases/TC-FULL-DEV-PROC-001/execution/p3_outputs/test_plan_ref.json
- done_definition: 必须产出 implementation_ref 与 candidate_artifacts_ref。
- handoff_note: 将 candidate_artifacts_ref 交接给 p5。
