# p6 协作上下文
- actor: admin
- target: subprocess:lifecycle-review
- purpose: 完成生命周期治理与 registry 同步前置校验。
- input_refs: docs/design/modules/evidence/bpm-runtime/w3c_full_development_cases/TC-FULL-DEV-PROC-001/execution/p5_outputs/final_gate_verdict_ref.json,review
- done_definition: 必须产出 lifecycle_transition_ref 与 registry_sync_ref。
- handoff_note: 将 lifecycle_transition_ref 与 registry_sync_ref 交接给 p7。
