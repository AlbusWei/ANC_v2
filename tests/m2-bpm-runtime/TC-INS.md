# TC-INS-001~005

## TC-INS-001 Root Instance Schema

- Input: create root instance (`stack_depth=0`) via process-instance runner.
- Expect:
  - `context.json` contains required fields: `session_binding`, `lineage_ref`, `stack_depth`, `process_version`, `process_level`.
  - `phase_results[0].session_id` exists.
  - `session_binding.json` exists and matches context payload.

## TC-INS-002 Child Stack Depth + Session Isolation

- Input: create child instance with `parent_instance_id` bound to root instance.
- Expect:
  - child `stack_depth = parent + 1`.
  - child `session_binding.parent_session_id = parent.session_binding.session_id`.
  - child `session_binding.session_id != parent.session_binding.session_id`.

## TC-INS-003 Parent Session Reuse Forbidden

- Input: force child `--session-id` to equal parent session id.
- Expect: command exits non-zero with fail-closed error.

## TC-INS-004 OpenClaw Dispatch Uses Explicit Session

- Input: create instance and inspect generated dispatch command.
- Expect:
  - dispatch command contains `--session-id`.
  - the argument value equals `session_binding.session_id`.

## TC-INS-005 Historical Migration + Replay

- Input: run migration for full `agents/control/BPM/memory/process_instances/`, then run replay validation.
- Expect:
  - migration report has `failed=0`.
  - replay report has `failed=0`.
  - no missing lineage/session fields in migrated instances.
