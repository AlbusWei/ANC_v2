# W2 Execution Summary - Governed Config Change Runtime Closure

## Scope

- Change: `m2-bpm-runtime-hardening`
- Thread: `W2`（配置治理流程运行闭环）
- Target key (low risk): `messages.groupChat.historyLimit`
- Test suite: `TC-GCC-001~003`
- Runner: `python3 tests/m2-bpm-runtime/run_tc_gcc.py`

## Live Patch + Rollback Result (TC-GCC-001)

- Before value: `124`
- After apply value: `125`
- After rollback value: `124`
- hash_before: `89bb0855d6dca1723052e97bf4217d026fd89bd4a821775cf54a3d50ab0c7028`
- hash_after_apply: `7458cf30a9419a6c441e1abfa310c72b0511dcd178b645ad68df795b1cdb4453`
- hash_after_rollback: `50b448656665aabed21c636720fc4257c2d83278106c476d8497b14d1e91bd09`
- Verdict: `pass`

备注：rollback 后 hash 不等于 hash_before（`meta.lastTouchedAt` 等元字段会变化），但值恢复和链路追溯完整。

## Reject Branch Result

### TC-GCC-002 (expired baseHash)

- Input: stale `base_hash`
- Output: `execution_status=failed`, `failure_code=base_hash_mismatch`
- Config hash unchanged during case execution
- Verdict: `pass`

### TC-GCC-003 (missing evidence)

- Input: `evidence_refs=[]`
- Output: gate `approval=deny`, process `verdict=deny`
- No apply stage executed
- Verdict: `pass`

## Evidence Index

- Suite report:
  - `docs/design/modules/evidence/bpm-runtime/w2_tc_gcc_report.json`
- Case outputs:
  - `docs/design/modules/evidence/bpm-runtime/w2_tc_gcc_cases/TC-GCC-001/process_output.json`
  - `docs/design/modules/evidence/bpm-runtime/w2_tc_gcc_cases/TC-GCC-001/evidence/verification_report.json`
  - `docs/design/modules/evidence/bpm-runtime/w2_tc_gcc_cases/TC-GCC-002/updater_output.json`
  - `docs/design/modules/evidence/bpm-runtime/w2_tc_gcc_cases/TC-GCC-003/process_output.json`
- Full evidence chain directory:
  - `docs/design/modules/evidence/bpm-runtime/w2_tc_gcc_cases/`
