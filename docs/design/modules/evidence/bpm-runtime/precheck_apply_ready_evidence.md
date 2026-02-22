# Thread 0 Precheck and Apply-Ready Evidence

## Scope

- Canonical root: `/Users/albus/MyProjects/ANC_v2/`
- This worktree: `/Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules` (`.` from this repository root)

## Entire / OpenClaw Preconditions (Executed 2026-02-22)

1. `entire status --detailed`
   - Result: `Enabled (manual-commit)`.
2. `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py start`
   - Result: `started_session=codex-b10136c2ff63`.
   - Transcript: `.entire/codex-bridge/transcript.json` (absolute: `/Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules/.entire/codex-bridge/transcript.json`).
3. `python3 /Users/albus/MyProjects/ANC_v2/tools/openclaw/switch_workspace.py --repo-root /Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules`
   - Result: `patch_result.ok=true`, `repo_root` points to current worktree, restart sentinel `status=ok`.
4. `openclaw config get agents.defaults.repoRoot --json`
   - Result: `/Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules`.
5. `openclaw config get skills.load.extraDirs --json`
   - Result: 6 entries, all under current worktree `processes/*` and `skills/*`.
6. `openclaw skills info config-change-gatekeeper --json`
   - Result: `eligible=true`, `filePath=/Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules/skills/system/config-change-gatekeeper/SKILL.md`.

Note:
- `openclaw config get` emitted a non-blocking warning: duplicate `matrix` plugin id. This did not affect the required precheck verdict.

## OpenSpec Apply-Ready Evidence

1. `openspec status --change "m2-bpm-runtime-hardening" --json`
   - Result: `schemaName="spec-driven"`, `isComplete=true`, `applyRequires=["tasks"]`, and all artifacts `status="done"`.
2. `openspec instructions apply --change "m2-bpm-runtime-hardening" --json`
   - Result: `state="ready"` (apply-ready).

## Baseline Scaffold Presence

- Test entry: `tests/m2-bpm-runtime/TEST.md`
- Regression runner: `tests/m2-bpm-runtime/run_post_dev_regression.py`
- Evidence directory: `docs/design/modules/evidence/bpm-runtime/`
- Placeholder files:
  - `docs/design/modules/evidence/bpm-runtime/checkpoint_commit_map.jsonl`
  - `docs/design/modules/evidence/bpm-runtime/git_range.txt`
- Plan file:
  - `docs/design/modules/evidence/bpm-runtime/m6_live_regression_plan.md`
