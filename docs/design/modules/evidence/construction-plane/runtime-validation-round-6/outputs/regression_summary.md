# M6 Runtime Validation Round 6 - Regression Summary

- generated_at: 2026-02-22T12:49:39.254237+00:00
- gate_decision: pass
- case_count: 13
- passed_count: 13
- failed_count: 0

## Case Results
- TC-001 [PASS] rc=0/0 registry verify pass
- TC-002 [PASS] rc=0/0 run_round scenario A
- TC-003 [PASS] rc=1/1 run_round scenario B
- TC-004 [PASS] rc=1/1 run_round scenario C
- TC-005 [PASS] rc=0/0 verify-m6 scenario A
- TC-006 [PASS] rc=1/1 verify-m6 scenario B
- TC-007 [PASS] rc=1/1 verify-m6 scenario C
- TC-008 [PASS] rc=0/0 construction-audit absolute output path pass
- TC-009 [PASS] rc=3/3 construction-audit missing registry fail closed
- TC-010 [PASS] rc=15/15 openspec-sync count mismatch fail closed
- TC-011 [PASS] rc=0/0 test-compiler m6 llm fixture
- TC-012 [PASS] rc=0/0 evaluation-runner llm available pass
- TC-013 [PASS] rc=20/20 evaluation-runner llm invalid model fail closed

## Reasons
- all_cases_passed
