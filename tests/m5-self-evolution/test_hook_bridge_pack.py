#!/usr/bin/env python3
"""Batch 8 Hook bridge 包测试（先测结构与 fail-closed 行为）。"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Tuple


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return payload


def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def make_repo_case_dir(case_key: str, tmp_path: Path) -> Path:
    root = repo_root()
    case_dir = root / "tmp" / "m5-self-evolution-tests" / f"{case_key}-{tmp_path.name}"
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


def hook_pack_root() -> Path:
    return repo_root() / "runtime_data/private-assets/hooks/anc-lifecycle-events"


def handler_path() -> Path:
    return hook_pack_root() / "hooks/lifecycle-event-bridge/handler.js"


def invoke_handler(event_payload: Dict[str, Any], case_dir: Path) -> Tuple[subprocess.CompletedProcess[str], Dict[str, Any]]:
    root = repo_root()
    event_path = case_dir / "event.json"
    dump_json(event_path, event_payload)

    runner = case_dir / "invoke_handler.mjs"
    runner.write_text(
        (
            "import fs from 'node:fs';\n"
            "import { pathToFileURL } from 'node:url';\n"
            "const handlerFile = process.argv[2];\n"
            "const eventFile = process.argv[3];\n"
            "const mod = await import(pathToFileURL(handlerFile).href);\n"
            "const event = JSON.parse(fs.readFileSync(eventFile, 'utf-8'));\n"
            "if (!Array.isArray(event.messages)) event.messages = [];\n"
            "await mod.default(event);\n"
            "process.stdout.write(JSON.stringify({ ok: true, messages: event.messages }) + '\\n');\n"
        ),
        encoding="utf-8",
    )

    proc = run_cmd(["node", str(runner), str(handler_path()), str(event_path)], root)
    payload: Dict[str, Any] = {}
    if proc.stdout.strip():
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    return proc, payload


def test_hook_pack_manifest_and_entries_exist() -> None:
    package_json = hook_pack_root() / "package.json"
    assert package_json.exists(), "hook pack package.json 缺失"
    pkg = load_json(package_json)
    hooks = (((pkg.get("openclaw") or {}).get("hooks")) if isinstance(pkg, dict) else None)
    assert isinstance(hooks, list) and hooks, "openclaw.hooks 必须为非空数组"

    for rel in hooks:
        hook_dir = hook_pack_root() / str(rel)
        assert (hook_dir / "HOOK.md").exists(), f"{hook_dir}/HOOK.md 缺失"
        assert (hook_dir / "handler.js").exists(), f"{hook_dir}/handler.js 缺失"


def test_hook_handler_fail_closed_local_catch(tmp_path: Path) -> None:
    case_dir = make_repo_case_dir("hook-fail-closed", tmp_path)
    bad_workspace = case_dir / "no-such-workspace"
    payload = {
        "type": "command",
        "action": "new",
        "sessionKey": "agent:main:main",
        "timestamp": "2026-03-03T12:00:00.000Z",
        "messages": [],
        "context": {
            "workspaceDir": str(bad_workspace),
            "commandSource": "pytest",
            "senderId": "qa",
        },
    }

    proc, result = invoke_handler(payload, case_dir)
    assert proc.returncode == 0, proc.stderr
    assert result.get("ok") is True


def test_hook_handler_writes_ingress_and_dispatch_request(tmp_path: Path) -> None:
    root = repo_root()
    case_dir = make_repo_case_dir("hook-ingress", tmp_path)
    workspace = root / "agents/kernel/admin"
    payload = {
        "type": "agent",
        "action": "bootstrap",
        "sessionKey": "agent:main:main",
        "timestamp": "2026-03-03T12:01:00.000Z",
        "messages": [],
        "context": {
            "workspaceDir": str(workspace),
            "commandSource": "pytest",
            "senderId": "qa",
        },
    }

    before = time.time()
    proc, result = invoke_handler(payload, case_dir)
    assert proc.returncode == 0, proc.stderr
    assert result.get("ok") is True

    ingress_dir = root / "runtime_data/evolution/hooks/ingress"
    dispatch_dir = root / "runtime_data/evolution/hooks/dispatch"
    assert ingress_dir.exists(), "ingress 目录未创建"
    assert dispatch_dir.exists(), "dispatch 目录未创建"

    # handler 采用异步派发，最多轮询 20 秒等待结果文件落盘。
    deadline = time.time() + 20
    newest_dispatch: Path | None = None
    while time.time() < deadline:
        files = sorted(dispatch_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
        if files and files[0].stat().st_mtime >= before:
            newest_dispatch = files[0]
            break
        time.sleep(0.5)

    assert newest_dispatch is not None, "dispatch 结果未在观察窗口内落盘"
    dispatch_payload = load_json(newest_dispatch)
    assert isinstance(dispatch_payload.get("runtime_output_ref"), str)
