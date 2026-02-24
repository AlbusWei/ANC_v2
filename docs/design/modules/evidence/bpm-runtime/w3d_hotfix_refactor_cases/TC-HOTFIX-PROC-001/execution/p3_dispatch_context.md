# p3 协作上下文
- actor: qa
- target: subprocess:quality-gate-preparation
- purpose: 围绕 hotfix 规格快速建立验证准备，优先覆盖线上风险链路。
- input_refs: docs/design/modules/evidence/bpm-runtime/w3d_hotfix_refactor_cases/TC-HOTFIX-PROC-001/execution/p2_outputs/spec_ref.json,docs/design/modules/evidence/bpm-runtime/w3d_hotfix_refactor_cases/TC-HOTFIX-PROC-001/execution/p2_outputs/hotfix_scope_baseline_ref.json
- done_definition: 必须产出 test_plan_ref 与 preparation_bundle_ref，并覆盖高风险回归点。
- handoff_note: 将 test_plan_ref 与 preparation_bundle_ref 交接给 p4。
