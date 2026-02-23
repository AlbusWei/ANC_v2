# p5 协作上下文
- actor: qa
- target: subprocess:quality-gate-evaluation
- purpose: 执行质量门禁评测并形成统一门禁结论。
- input_refs: docs/design/modules/evidence/bpm-runtime/w3c_full_development_cases/TC-FULL-DEV-PROC-001/execution/p4_outputs/candidate_artifacts_ref.json,docs/design/modules/evidence/bpm-runtime/w3c_full_development_cases/TC-FULL-DEV-PROC-001/execution/p3_outputs/preparation_bundle_ref.json
- done_definition: 必须产出 final_gate_verdict_ref，且门禁结论可解释。
- handoff_note: 若门禁通过，则将 final_gate_verdict_ref 交接给 p6。
