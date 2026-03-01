# Entire Codex Bridge Contract

## Purpose

Document the compatibility assumptions behind `scripts/entire_codex_bridge.py`.

## Hook Contract Used

The bridge drives internal Entire hook commands:

1. `entire hooks gemini session-start`
2. `entire hooks gemini before-agent`
3. `entire hooks gemini after-agent`
4. `entire hooks gemini session-end`

Each hook receives JSON with at least:

- `session_id`
- `transcript_path`
- `cwd`
- `timestamp`

`before-agent` also includes:

- `prompt`

## Transcript Format Used

The bridge writes a Gemini-compatible transcript JSON file:

```json
{
  "messages": [
    {"id":"user-...","type":"user","content":"..."},
    {"id":"gemini-...","type":"gemini","content":"...","toolCalls":[...]}
  ]
}
```

`toolCalls` entries use `name: "write_file"` and `args.file_path`.

## Failure Model

Fail closed when:

1. Not inside a Git repository
2. `entire` is not installed
3. `entire status` fails or reports disabled
4. Any hook invocation returns non-zero
5. Transcript/state JSON becomes invalid

## Compatibility Caveat

This bridge is **Codex-only** and intentionally drives `gemini` hook compatibility paths.
Do not call it from Claude Code runtime; Claude Code has native `claude-code` hooks and
using this bridge there will mis-attribute provider identity to Gemini.

If this behavior changes in future Entire versions, re-validate against:

- `entire version`
- `entire hooks --help`
- `docs.entire.io/cli/commands`

