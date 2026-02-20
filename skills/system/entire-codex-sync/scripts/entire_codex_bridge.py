#!/usr/bin/env python3
"""
Bridge Codex-driven work to Entire by driving the Gemini hook lifecycle manually.

This script is intentionally small and dependency-free so it can run anywhere that
has Python 3 and the `entire` CLI available.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DIR_REL = ".entire/codex-bridge"
STATE_FILE_NAME = "session.json"
TRANSCRIPT_FILE_NAME = "transcript.json"


class BridgeError(RuntimeError):
    """Raised for fail-closed bridge errors."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run(
    cmd: list[str],
    cwd: Path,
    stdin_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        input=stdin_text,
        capture_output=True,
        text=True,
        check=check,
    )


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise BridgeError("Not inside a git repository. Cannot run Entire bridge.")
    return Path(proc.stdout.strip()).resolve()


def ensure_entire_enabled(root: Path) -> None:
    if shutil.which("entire") is None:
        raise BridgeError("`entire` command not found in PATH.")

    status_proc = run(["entire", "status"], cwd=root, check=False)
    if status_proc.returncode != 0:
        raise BridgeError(f"`entire status` failed:\n{status_proc.stderr.strip()}")

    if "enabled" not in status_proc.stdout.lower():
        raise BridgeError(
            "Entire is not enabled in this repository. Run `entire enable` first."
        )


@dataclass
class BridgeSession:
    session_id: str
    transcript_path: Path
    started_at: str
    turns: int
    active: bool

    @staticmethod
    def from_dict(data: dict[str, Any], root: Path) -> "BridgeSession":
        return BridgeSession(
            session_id=str(data["session_id"]),
            transcript_path=(root / data["transcript_path"]).resolve(),
            started_at=str(data.get("started_at", now_iso())),
            turns=int(data.get("turns", 0)),
            active=bool(data.get("active", True)),
        )

    def to_dict(self, root: Path) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "transcript_path": os.path.relpath(self.transcript_path, root),
            "started_at": self.started_at,
            "turns": self.turns,
            "active": self.active,
        }


def state_paths(root: Path) -> tuple[Path, Path, Path]:
    bridge_dir = root / STATE_DIR_REL
    state_file = bridge_dir / STATE_FILE_NAME
    transcript_file = bridge_dir / TRANSCRIPT_FILE_NAME
    return bridge_dir, state_file, transcript_file


def load_session(root: Path) -> BridgeSession | None:
    _, state_file, _ = state_paths(root)
    if not state_file.exists():
        return None
    try:
        raw = json.loads(state_file.read_text(encoding="utf-8"))
        return BridgeSession.from_dict(raw, root)
    except Exception as exc:  # pragma: no cover - defensive
        raise BridgeError(f"Invalid bridge state file: {state_file} ({exc})") from exc


def save_session(root: Path, session: BridgeSession) -> None:
    bridge_dir, state_file, _ = state_paths(root)
    bridge_dir.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(session.to_dict(root), ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def load_transcript(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"messages": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BridgeError(f"Transcript is not valid JSON: {path}") from exc
    if not isinstance(data, dict) or "messages" not in data:
        raise BridgeError(f"Transcript has invalid schema: {path}")
    if not isinstance(data["messages"], list):
        raise BridgeError(f"Transcript.messages is not a list: {path}")
    return data


def save_transcript(path: Path, transcript: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(transcript, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )


def payload(session: BridgeSession, root: Path, prompt: str | None = None) -> str:
    data: dict[str, Any] = {
        "session_id": session.session_id,
        "transcript_path": str(session.transcript_path),
        "cwd": str(root),
        "timestamp": now_iso(),
    }
    if prompt:
        data["prompt"] = prompt
    return json.dumps(data, ensure_ascii=True)


def call_hook(root: Path, hook_name: str, json_payload: str) -> None:
    proc = run(
        ["entire", "hooks", "gemini", hook_name],
        cwd=root,
        stdin_text=json_payload + "\n",
        check=False,
    )
    if proc.returncode != 0:
        raise BridgeError(
            f"`entire hooks gemini {hook_name}` failed:\n"
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )


def ensure_active_session(root: Path) -> BridgeSession:
    session = load_session(root)
    if session and session.active:
        return session

    _, _, transcript_file = state_paths(root)
    if not transcript_file.exists():
        save_transcript(transcript_file, {"messages": []})

    session = BridgeSession(
        session_id=f"codex-{uuid.uuid4().hex[:12]}",
        transcript_path=transcript_file,
        started_at=now_iso(),
        turns=0,
        active=True,
    )
    call_hook(root, "session-start", payload(session, root))
    save_session(root, session)
    return session


def normalize_file(root: Path, file_path: str) -> str:
    candidate = Path(file_path)
    if candidate.is_absolute():
        try:
            return str(candidate.resolve().relative_to(root))
        except ValueError:
            return str(candidate.resolve())
    return str((root / candidate).resolve().relative_to(root))


def append_turn(
    root: Path,
    session: BridgeSession,
    prompt_text: str,
    summary_text: str,
    files: list[str],
) -> None:
    transcript = load_transcript(session.transcript_path)
    messages = transcript["messages"]

    user_id = f"user-{uuid.uuid4().hex[:10]}"
    assistant_id = f"gemini-{uuid.uuid4().hex[:10]}"
    tool_calls: list[dict[str, Any]] = []
    for idx, f in enumerate(files, start=1):
        normalized = normalize_file(root, f)
        tool_calls.append(
            {
                "id": f"tool-{idx}-{uuid.uuid4().hex[:8]}",
                "name": "write_file",
                "args": {"file_path": normalized},
                "status": "success",
            }
        )

    messages.append({"id": user_id, "type": "user", "content": prompt_text})
    assistant_msg: dict[str, Any] = {
        "id": assistant_id,
        "type": "gemini",
        "content": summary_text,
    }
    if tool_calls:
        assistant_msg["toolCalls"] = tool_calls
    messages.append(assistant_msg)
    save_transcript(session.transcript_path, transcript)


def cmd_status(root: Path) -> int:
    session = load_session(root)
    if not session:
        print("bridge_session=none")
        return 0
    print(f"bridge_session_id={session.session_id}")
    print(f"bridge_active={str(session.active).lower()}")
    print(f"bridge_turns={session.turns}")
    print(f"bridge_transcript={session.transcript_path}")
    return 0


def cmd_start(root: Path) -> int:
    session = ensure_active_session(root)
    print(f"started_session={session.session_id}")
    print(f"transcript={session.transcript_path}")
    return 0


def cmd_sync(root: Path, prompt_text: str, summary_text: str, files: list[str]) -> int:
    if not prompt_text.strip():
        raise BridgeError("`--prompt` cannot be empty.")
    if not summary_text.strip():
        raise BridgeError("`--summary` cannot be empty.")

    session = ensure_active_session(root)
    call_hook(root, "before-agent", payload(session, root, prompt=prompt_text.strip()))
    append_turn(root, session, prompt_text.strip(), summary_text.strip(), files)
    call_hook(root, "after-agent", payload(session, root))

    session.turns += 1
    save_session(root, session)
    print(f"synced_session={session.session_id}")
    print(f"synced_turn={session.turns}")
    if files:
        print("synced_files=" + ",".join(normalize_file(root, f) for f in files))
    return 0


def cmd_end(root: Path) -> int:
    session = load_session(root)
    if not session or not session.active:
        print("bridge_session=already-ended")
        return 0

    call_hook(root, "session-end", payload(session, root))
    session.active = False
    save_session(root, session)
    print(f"ended_session={session.session_id}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bridge Codex development turns to Entire checkpoints."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show current bridge session status")
    sub.add_parser("start", help="Start or reuse an active bridge session")

    sync = sub.add_parser("sync", help="Sync one Codex development turn")
    sync.add_argument("--prompt", required=True, help="User prompt for this turn")
    sync.add_argument(
        "--summary",
        required=True,
        help="Assistant summary for this turn (stored in transcript)",
    )
    sync.add_argument(
        "--files",
        nargs="*",
        default=[],
        help="Files modified in this turn (relative or absolute paths)",
    )

    sub.add_parser("end", help="End the active bridge session")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        root = repo_root()
        ensure_entire_enabled(root)

        if args.command == "status":
            return cmd_status(root)
        if args.command == "start":
            return cmd_start(root)
        if args.command == "sync":
            return cmd_sync(root, args.prompt, args.summary, args.files)
        if args.command == "end":
            return cmd_end(root)
        raise BridgeError(f"Unsupported command: {args.command}")
    except BridgeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
