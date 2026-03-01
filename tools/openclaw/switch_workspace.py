#!/usr/bin/env python3
"""Switch OpenClaw runtime workspace/config to a target ANC_v2 repo or worktree.

This script is fail-closed:
1. Validates projection freshness for the selected scope profile.
2. Expands repo-relative agents.list and skill/process source dirs to absolute paths.
3. Applies hash-safe config.patch with baseHash.
4. Verifies the key config fields after patch.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Tuple


SCOPE_TO_PROFILE = {
    "public": "phase05-base",
    "dev": "phase05-with-entry",
}
DEFAULT_PRIVATE_OVERLAY = "runtime_data/private-assets/openclaw.overlay.json"


def _parse_json_from_mixed_output(text: str) -> Any:
    """Extract JSON payload from CLI output that may include warning lines."""
    decoder = json.JSONDecoder()
    fallback = None
    for idx, ch in enumerate(text):
        if ch not in "[{":
            continue
        try:
            value, end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        remainder = text[idx + end :].strip()
        if not remainder:
            return value
        fallback = value
    if fallback is not None:
        return fallback

    # Some `openclaw config get ... --json` commands return scalar JSON
    # (for example a quoted string) on a single line.
    for line in reversed(text.splitlines()):
        raw = line.strip()
        if not raw:
            continue
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            continue
    raise RuntimeError("No JSON payload found in command output.")


def _run(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)


def _openclaw_cmd(profile: str | None, *args: str) -> List[str]:
    cmd = ["openclaw"]
    if profile:
        cmd.extend(["--profile", profile])
    cmd.extend(args)
    return cmd


def _require_ok(proc: subprocess.CompletedProcess[str], cmd: List[str], hint: str = "") -> str:
    if proc.returncode == 0:
        return proc.stdout
    detail = [f"Command failed ({proc.returncode}): {' '.join(cmd)}"]
    if hint:
        detail.append(hint)
    if proc.stdout.strip():
        detail.append("STDOUT:")
        detail.append(proc.stdout.strip())
    if proc.stderr.strip():
        detail.append("STDERR:")
        detail.append(proc.stderr.strip())
    raise RuntimeError("\n".join(detail))


def _ensure_exists(path: Path, desc: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Missing {desc}: {path}")


def _load_json_file(path: Path, desc: str) -> Dict[str, Any]:
    _ensure_exists(path, desc)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {desc}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{desc} root must be object: {path}")
    return payload


def _resolve_fragment_from_scope(repo_root: Path, scope: str) -> Tuple[Path, str]:
    profile_key = SCOPE_TO_PROFILE.get(scope)
    if not profile_key:
        raise RuntimeError(f"Unsupported scope: {scope}")

    profiles_path = repo_root / "config/openclaw.projection.profiles.json"
    profiles_payload = _load_json_file(profiles_path, "projection profiles")

    profiles = profiles_payload.get("profiles")
    if not isinstance(profiles, dict):
        raise RuntimeError("Invalid projection profiles: missing object 'profiles'")

    profile_cfg = profiles.get(profile_key)
    if not isinstance(profile_cfg, dict):
        raise RuntimeError(f"Profile not found in projection profiles: {profile_key}")

    output_file = profile_cfg.get("output_file")
    if not isinstance(output_file, str) or not output_file.strip():
        raise RuntimeError(f"Profile {profile_key} missing output_file")

    fragment_path = (repo_root / output_file).resolve()
    return fragment_path, profile_key


def _merge_fragment(base_fragment: Dict[str, Any], overlay_fragment: Dict[str, Any]) -> Dict[str, Any]:
    """Merge overlay into base for agents.list and skills.entries only."""
    merged = deepcopy(base_fragment)

    base_agents = merged.setdefault("agents", {}).setdefault("list", [])
    if not isinstance(base_agents, list):
        raise RuntimeError("Invalid base fragment: agents.list must be array")

    agents_by_id: Dict[str, Dict[str, str]] = {}
    order: List[str] = []
    for raw in base_agents:
        if not isinstance(raw, dict):
            raise RuntimeError(f"Invalid base fragment agent entry: {raw!r}")
        agent_id = raw.get("id")
        workspace = raw.get("workspace")
        if not isinstance(agent_id, str) or not agent_id.strip() or not isinstance(workspace, str) or not workspace.strip():
            raise RuntimeError(f"Invalid base fragment agent entry: {raw!r}")
        agents_by_id[agent_id] = {"id": agent_id, "workspace": workspace}
        order.append(agent_id)

    overlay_agents = overlay_fragment.get("agents", {}).get("list", [])
    if overlay_agents is None:
        overlay_agents = []
    if not isinstance(overlay_agents, list):
        raise RuntimeError("Invalid private overlay: agents.list must be array")

    for raw in overlay_agents:
        if not isinstance(raw, dict):
            raise RuntimeError(f"Invalid private overlay agent entry: {raw!r}")
        agent_id = raw.get("id")
        workspace = raw.get("workspace")
        if not isinstance(agent_id, str) or not agent_id.strip() or not isinstance(workspace, str) or not workspace.strip():
            raise RuntimeError(f"Invalid private overlay agent entry: {raw!r}")
        agents_by_id[agent_id] = {"id": agent_id, "workspace": workspace}
        if agent_id not in order:
            order.append(agent_id)

    merged["agents"]["list"] = [agents_by_id[agent_id] for agent_id in order]

    base_entries = merged.setdefault("skills", {}).setdefault("entries", {})
    if not isinstance(base_entries, dict):
        raise RuntimeError("Invalid base fragment: skills.entries must be object")

    overlay_entries = overlay_fragment.get("skills", {}).get("entries", {})
    if overlay_entries is None:
        overlay_entries = {}
    if not isinstance(overlay_entries, dict):
        raise RuntimeError("Invalid private overlay: skills.entries must be object")

    for entry_key, entry_val in overlay_entries.items():
        if not isinstance(entry_key, str) or not entry_key.strip() or not isinstance(entry_val, dict):
            raise RuntimeError(f"Invalid private overlay skills entry: {entry_key!r}={entry_val!r}")
        base_entries[entry_key] = entry_val

    return merged


def _inject_private_skill_entries(fragment: Dict[str, Any], repo_root: Path) -> List[str]:
    """Inject default private skill/process dirs when they exist."""
    injected: List[str] = []
    entries = fragment.setdefault("skills", {}).setdefault("entries", {})
    if not isinstance(entries, dict):
        raise RuntimeError("Invalid fragment: skills.entries must be object")

    defaults = [
        ("private-anc-processes", "runtime_data/private-assets/processes"),
        ("private-anc-skills", "runtime_data/private-assets/skills"),
    ]
    for entry_key, rel_source in defaults:
        if entry_key in entries:
            continue
        if (repo_root / rel_source).exists():
            entries[entry_key] = {"source": rel_source}
            injected.append(rel_source)
    return injected


def _build_patch(repo_root: Path, fragment: Dict[str, Any], current_config: Dict[str, Any]) -> Dict[str, Any]:
    agents_list: List[Dict[str, str]] = []
    agent_id_order: List[str] = []
    for item in fragment.get("agents", {}).get("list", []):
        agent_id = item.get("id")
        workspace_rel = item.get("workspace")
        if not agent_id or not workspace_rel:
            raise RuntimeError(f"Invalid agents.list entry in fragment: {item!r}")
        workspace_abs = (repo_root / workspace_rel).resolve()
        _ensure_exists(workspace_abs, f"agent workspace for {agent_id}")
        agents_list.append({"id": agent_id, "workspace": str(workspace_abs)})
        agent_id_order.append(agent_id)

    if not agents_list:
        raise RuntimeError("Fragment agents.list is empty.")

    skill_source_dirs: List[str] = []
    seen_source_dirs = set()
    for entry_key, entry_val in fragment.get("skills", {}).get("entries", {}).items():
        source_rel = entry_val.get("source")
        if not source_rel:
            raise RuntimeError(f"Invalid skills.entries item for {entry_key!r}: {entry_val!r}")
        source_abs = (repo_root / source_rel).resolve()
        _ensure_exists(source_abs, f"skill/process source dir for {entry_key}")
        source_str = str(source_abs)
        if source_str in seen_source_dirs:
            continue
        seen_source_dirs.add(source_str)
        skill_source_dirs.append(source_str)

    preferred_default_ids = ["personal-assistant", "admin", "kernel-dev"]
    default_agent_id = next(
        (agent_id for agent_id in preferred_default_ids if agent_id in agent_id_order),
        agent_id_order[0],
    )
    default_workspace = next(item["workspace"] for item in agents_list if item["id"] == default_agent_id)

    patch: Dict[str, Any] = {
        "agents": {
            "defaults": {
                "workspace": default_workspace,
                "repoRoot": str(repo_root),
            },
            "list": agents_list,
        },
        "skills": {"load": {"extraDirs": skill_source_dirs}},
        "tools": {"agentToAgent": {"allow": agent_id_order}},
    }

    # Keep existing binding rules but remap invalid agentId to the selected default.
    existing_bindings = current_config.get("bindings")
    if isinstance(existing_bindings, list):
        valid_ids = set(agent_id_order)
        rewritten_bindings = []
        changed = False
        for raw in existing_bindings:
            if not isinstance(raw, dict):
                rewritten_bindings.append(raw)
                continue
            item = dict(raw)
            if item.get("agentId") not in valid_ids:
                item["agentId"] = default_agent_id
                changed = True
            rewritten_bindings.append(item)
        if changed:
            patch["bindings"] = rewritten_bindings

    return patch


def _verify_after_patch(
    repo_root: Path,
    profile: str | None,
    expected_agents: List[Dict[str, str]],
    expected_repo_root: str,
    expected_skill_source_dirs: List[str],
) -> None:
    agents_out = _require_ok(
        _run(_openclaw_cmd(profile, "config", "get", "agents.list", "--json"), repo_root),
        _openclaw_cmd(profile, "config", "get", "agents.list", "--json"),
    )
    actual_agents = _parse_json_from_mixed_output(agents_out)
    if actual_agents != expected_agents:
        raise RuntimeError(
            "Verification failed: agents.list mismatch.\n"
            f"Expected: {json.dumps(expected_agents, ensure_ascii=False)}\n"
            f"Actual: {json.dumps(actual_agents, ensure_ascii=False)}"
        )

    repo_root_out = _require_ok(
        _run(_openclaw_cmd(profile, "config", "get", "agents.defaults.repoRoot", "--json"), repo_root),
        _openclaw_cmd(profile, "config", "get", "agents.defaults.repoRoot", "--json"),
    )
    actual_repo_root = _parse_json_from_mixed_output(repo_root_out)
    if actual_repo_root != expected_repo_root:
        raise RuntimeError(
            "Verification failed: agents.defaults.repoRoot mismatch.\n"
            f"Expected: {expected_repo_root}\nActual: {actual_repo_root}"
        )

    skills_out = _require_ok(
        _run(_openclaw_cmd(profile, "config", "get", "skills.load.extraDirs", "--json"), repo_root),
        _openclaw_cmd(profile, "config", "get", "skills.load.extraDirs", "--json"),
    )
    actual_skill_source_dirs = _parse_json_from_mixed_output(skills_out)
    if actual_skill_source_dirs != expected_skill_source_dirs:
        raise RuntimeError(
            "Verification failed: skills.load.extraDirs mismatch.\n"
            f"Expected: {json.dumps(expected_skill_source_dirs, ensure_ascii=False)}\n"
            f"Actual: {json.dumps(actual_skill_source_dirs, ensure_ascii=False)}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Switch OpenClaw workspace/config to target ANC_v2 repo or worktree root."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Target ANC_v2 repo/worktree root (default: current directory).",
    )
    parser.add_argument(
        "--scope",
        choices=["public", "dev"],
        default="dev",
        help="public=phase05-base; dev=phase05-with-entry (default: dev).",
    )
    parser.add_argument(
        "--fragment",
        help="Path to projected fragment JSON (default depends on --scope and config/openclaw.projection.profiles.json).",
    )
    parser.add_argument(
        "--openclaw-profile",
        default="",
        help="Optional OpenClaw profile name (maps to: openclaw --profile <name> ...).",
    )
    parser.add_argument(
        "--skip-projection-check",
        action="store_true",
        help="Skip registry projection freshness check (not recommended).",
    )
    parser.add_argument(
        "--enable-private-assets",
        action="store_true",
        help="Merge runtime_data/private-assets overlay and private skill/process dirs when available.",
    )
    parser.add_argument(
        "--private-overlay",
        default="",
        help=(
            "Private overlay JSON path (repo-relative or absolute). "
            "Default: runtime_data/private-assets/openclaw.overlay.json"
        ),
    )
    parser.add_argument(
        "--require-private-overlay",
        action="store_true",
        help="Fail when --enable-private-assets is set but private overlay file is missing.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print patch without applying it.")
    parser.add_argument(
        "--receipt-file",
        help="Optional file path to write switch receipt JSON.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    registry_tool = repo_root / "shared/registry/registry_contract_tool.py"
    profile = args.openclaw_profile.strip() or None

    _ensure_exists(repo_root, "repo root")
    _ensure_exists(registry_tool, "registry_contract_tool.py")

    if args.fragment:
        fragment_path = Path(args.fragment).expanduser().resolve()
        projection_profile = SCOPE_TO_PROFILE[args.scope]
    else:
        fragment_path, projection_profile = _resolve_fragment_from_scope(repo_root, args.scope)
    _ensure_exists(fragment_path, "OpenClaw fragment")

    if not args.skip_projection_check:
        check_cmd = [
            "python3",
            str(registry_tool),
            "project-openclaw",
            "--profile",
            projection_profile,
            "--check",
        ]
        check_proc = _run(check_cmd, repo_root)
        _require_ok(
            check_proc,
            check_cmd,
            hint=(
                "Projection is stale or invalid. Run:\n"
                f"python3 shared/registry/registry_contract_tool.py project-openclaw --profile {projection_profile}"
            ),
        )

    fragment = _load_json_file(fragment_path, "OpenClaw fragment")

    private_overlay_path = Path(args.private_overlay) if args.private_overlay else Path(DEFAULT_PRIVATE_OVERLAY)
    private_overlay_path = (
        private_overlay_path.expanduser().resolve()
        if private_overlay_path.is_absolute()
        else (repo_root / private_overlay_path).resolve()
    )

    private_overlay_applied = False
    private_auto_skill_sources: List[str] = []
    if args.enable_private_assets:
        private_auto_skill_sources = _inject_private_skill_entries(fragment, repo_root)
        if private_overlay_path.exists():
            private_overlay = _load_json_file(private_overlay_path, "private overlay")
            fragment = _merge_fragment(fragment, private_overlay)
            private_overlay_applied = True
        elif args.require_private_overlay:
            raise RuntimeError(
                "Private overlay required but missing: "
                f"{private_overlay_path}. Provide --private-overlay or create the default overlay file."
            )

    cfg_get_cmd = _openclaw_cmd(profile, "gateway", "call", "config.get", "--params", "{}", "--json")
    cfg_proc = _run(cfg_get_cmd, repo_root)
    cfg_stdout = _require_ok(
        cfg_proc,
        cfg_get_cmd,
        hint="OpenClaw gateway call failed. Ensure gateway is healthy and reachable.",
    )
    cfg_payload = _parse_json_from_mixed_output(cfg_stdout)

    current_config = cfg_payload.get("parsed") or cfg_payload.get("config")
    base_hash = cfg_payload.get("hash")
    if not isinstance(current_config, dict) or not base_hash:
        raise RuntimeError("Unexpected config.get payload: missing parsed/config or hash.")

    patch = _build_patch(repo_root, fragment, current_config)
    params = {"raw": json.dumps(patch, ensure_ascii=False), "baseHash": base_hash}

    receipt: Dict[str, Any] = {
        "repo_root": str(repo_root),
        "scope": args.scope,
        "projection_profile": projection_profile,
        "fragment": str(fragment_path),
        "private_assets_enabled": bool(args.enable_private_assets),
        "private_overlay": str(private_overlay_path),
        "private_overlay_applied": private_overlay_applied,
        "private_auto_skill_sources": private_auto_skill_sources,
        "openclaw_profile": profile or "default",
        "base_hash": base_hash,
        "agent_count": len(patch["agents"]["list"]),
        "agent_ids": [item["id"] for item in patch["agents"]["list"]],
        "default_workspace": patch["agents"]["defaults"]["workspace"],
        "skill_source_dirs": patch["skills"]["load"]["extraDirs"],
        "dry_run": bool(args.dry_run),
    }

    if args.dry_run:
        receipt["patch"] = patch
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0

    patch_cmd = _openclaw_cmd(
        profile,
        "gateway",
        "call",
        "config.patch",
        "--params",
        json.dumps(params, ensure_ascii=False),
        "--json",
    )
    patch_proc = _run(patch_cmd, repo_root)
    patch_stdout = _require_ok(
        patch_proc,
        patch_cmd,
        hint="config.patch failed; no success receipt returned.",
    )
    patch_payload = _parse_json_from_mixed_output(patch_stdout)

    if isinstance(patch_payload, dict):
        receipt["patch_result"] = patch_payload
        if patch_payload.get("ok") is False:
            raise RuntimeError(f"OpenClaw rejected patch: {json.dumps(patch_payload, ensure_ascii=False)}")

    _verify_after_patch(
        repo_root=repo_root,
        profile=profile,
        expected_agents=patch["agents"]["list"],
        expected_repo_root=str(repo_root),
        expected_skill_source_dirs=patch["skills"]["load"]["extraDirs"],
    )

    if args.receipt_file:
        receipt_file = Path(args.receipt_file).expanduser().resolve()
        receipt_file.parent.mkdir(parents=True, exist_ok=True)
        receipt_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipt["receipt_file"] = str(receipt_file)

    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
