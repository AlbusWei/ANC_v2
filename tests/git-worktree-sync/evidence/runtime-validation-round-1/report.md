# git-worktree-sync Runtime Validation Report

- gate_decision: pass
- summary_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/run_summary.json

## Case Results
### TC-001 integrate dry-run returns plan
- decision: pass
- return_code: 0 (expected 0)
- payload_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-001/payload.json
- stdout_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-001/stdout.txt
- stderr_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-001/stderr.txt
- reasons: (none)

### TC-002 fanout skips dirty sibling above threshold
- decision: pass
- return_code: 0 (expected 0)
- payload_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-002/payload.json
- stdout_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-002/stdout.txt
- stderr_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-002/stderr.txt
- reasons: (none)

### TC-003 fanout conflict triggers manual_conflict and merge abort
- decision: pass
- return_code: 4 (expected 4)
- payload_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-003/payload.json
- stdout_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-003/stdout.txt
- stderr_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-003/stderr.txt
- reasons: (none)

### TC-004 fanout includes latest commit from non-default upstream remote
- decision: pass
- return_code: 0 (expected 0)
- payload_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-004/payload.json
- stdout_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-004/stdout.txt
- stderr_ref: tests/git-worktree-sync/evidence/runtime-validation-round-1/outputs/TC-004/stderr.txt
- reasons: (none)

## Gate Reasons
- all P0 cases passed
