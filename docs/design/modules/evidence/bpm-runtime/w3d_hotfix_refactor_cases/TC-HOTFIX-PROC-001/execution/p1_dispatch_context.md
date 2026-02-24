# p1 协作上下文
- actor: architect
- target: subprocess:hotfix-intake-normalization
- purpose: 在应急场景先把问题定义收敛为可执行修复目标，避免团队直接在模糊告警上动手。
- input_refs: docs/design/modules/evidence/bpm-runtime/w3d_hotfix_refactor_cases/TC-HOTFIX-PROC-001/incident_context.md,docs/design/modules/evidence/bpm-runtime/w3d_hotfix_refactor_cases/TC-HOTFIX-PROC-001/target_asset.md
- done_definition: 必须产出 hotfix_objective_ref、impact_scope_ref、rollback_direction_ref，并明确爆炸半径。
- handoff_note: 将 hotfix_objective_ref、impact_scope_ref、rollback_direction_ref 交接给 p2，作为快速规格输入。
