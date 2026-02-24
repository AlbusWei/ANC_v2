# p2 协作上下文
- actor: architect
- target: subprocess:hotfix-scope-spec-baseline
- purpose: 把应急目标压缩为可执行范围与规格，明确不做什么，控制修复面。
- input_refs: docs/design/modules/evidence/bpm-runtime/w3d_hotfix_refactor_cases/TC-HOTFIX-PROC-001/execution/p1_outputs/hotfix_objective_ref.json,docs/design/modules/evidence/bpm-runtime/w3d_hotfix_refactor_cases/TC-HOTFIX-PROC-001/execution/p1_outputs/impact_scope_ref.json,docs/design/modules/evidence/bpm-runtime/w3d_hotfix_refactor_cases/TC-HOTFIX-PROC-001/execution/p1_outputs/rollback_direction_ref.json
- done_definition: 必须产出 hotfix_scope_baseline_ref 与 spec_ref，且规格包含回滚约束。
- handoff_note: 将 hotfix_scope_baseline_ref 与 spec_ref 交接给 p3。
