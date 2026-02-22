# Thread 0 Precheck and Apply-Ready Evidence

## Entire / OpenClaw Preconditions

1. `entire status --detailed`
   - Result: `Enabled (manual-commit)`
2. `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py start`
   - Result: started session and transcript path created.
3. `python3 /Users/albus/MyProjects/ANC_v2/tools/openclaw/switch_workspace.py --repo-root /Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules`
   - Result: patch applied with `ok: true`, restart sentinel `status: ok`.
4. `openclaw config get agents.defaults.repoRoot --json`
   - Result: `/Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules`
5. `openclaw config get skills.load.extraDirs --json`
   - Result: includes current worktree `processes/*` and `skills/*` extra dirs.
6. `openclaw skills info config-change-gatekeeper --json`
   - Result: `eligible: true`, skill path points to current worktree.

## OpenSpec Apply-Ready Evidence

1. Initial check:
   - `openspec status --change "m2-bpm-runtime-hardening" --json`
   - Result: `Change not found`
2. Scaffold created:
   - `openspec new change "m2-bpm-runtime-hardening"`
3. Artifacts created:
   - `proposal.md`
   - `specs/bpm-runtime-hardening-audit-foundation/spec.md`
   - `specs/construction-plane/spec.md`
   - `design.md`
   - `tasks.md`
4. Final check:
   - `openspec instructions apply --change "m2-bpm-runtime-hardening" --json`
   - Result: `state: "ready"`

## Timestamp (UTC)

- `2026-02-22T12:41:00Z` to `2026-02-22T12:42:30Z` (Thread 0 execution window)
