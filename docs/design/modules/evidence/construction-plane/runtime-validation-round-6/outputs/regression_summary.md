# M6 Runtime Validation Round 6 - Regression Summary

- generated_at: 2026-02-22T19:09:01.107572+00:00
- gate_decision: fail
- case_count: 13
- passed_count: 9
- failed_count: 4

## Case Results
- TC-001 [PASS] rc=0/0 registry verify pass
- TC-002 [FAIL] rc=1/0 run_round scenario A
- TC-003 [FAIL] rc=1/1 run_round scenario B
- TC-004 [PASS] rc=1/1 run_round scenario C
- TC-005 [FAIL] rc=1/0 verify-m6 scenario A
- TC-006 [FAIL] rc=1/1 verify-m6 scenario B
- TC-007 [PASS] rc=1/1 verify-m6 scenario C
- TC-008 [PASS] rc=0/0 construction-audit absolute output path pass
- TC-009 [PASS] rc=3/3 construction-audit missing registry fail closed
- TC-010 [PASS] rc=15/15 openspec-sync count mismatch fail closed
- TC-011 [PASS] rc=0/0 test-compiler m6 llm fixture
- TC-012 [PASS] rc=0/0 evaluation-runner llm available pass
- TC-013 [PASS] rc=20/20 evaluation-runner llm invalid model fail closed

## Reasons
- TC-002:return_code_mismatch:1!=0;round_status_mismatch:failed!=passed
- TC-003:failed_phase_mismatch:p4!=p5
- TC-005:return_code_mismatch:1!=0;stdout_missing:verify-m6 passed
- TC-006:stderr_missing:checkpoint_count must equal commit_count
