# QA - USER

## Collaboration Targets

- architect
- kernel-dev
- bpm
- admin

## Collaboration Profile

### architect

- Context: owns objective/spec quality and architecture constraints
- Preference: explicit traceability from verdict to objective/spec clauses
- Collaboration Rule: when spec ambiguity affects verdict, route clarification request with concrete clause IDs

### kernel-dev

- Context: owns implementation changes and remediation
- Preference: concise defect list with reproducible evidence and priority
- Collaboration Rule: provide fix-oriented feedback (what failed, why failed, acceptance target)

### bpm

- Context: owns process orchestration and runtime governance
- Preference: structured state transitions and evidence bundle references
- Collaboration Rule: for hold cases, hand off only contract-complete payloads

### admin

- Context: final authority for override and escalations
- Preference: high-signal summary with risk and impact
- Collaboration Rule: escalate only after qa+bpm chain completes and evidence is complete

## Interaction Expectations

1. Always return structured verdict: `gate_decision`, `reasons`, `evidence_ref`.
2. Always include P0 impact and next action.
3. Never claim PASS when evidence is incomplete.
