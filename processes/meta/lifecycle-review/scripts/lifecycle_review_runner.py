#!/usr/bin/env python3
"""Minimal executable runner for lifecycle-review process."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


class LifecycleReviewError(RuntimeError):
    """Fail-closed runtime error for lifecycle-review."""


ALLOWED_STATES = {"draft", "review", "active", "deprecated", "retired"}
ALLOWED_TRANSITIONS = {
    "draft": {"review"},
    "review": {"active", "deprecated"},
    "active": {"deprecated"},
    "deprecated": {"retired"},
    "retired": set(),
}
PASS_DECISIONS = {"pass", "approved", "go"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise LifecycleReviewError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LifecycleReviewError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LifecycleReviewError(f"invalid json: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise LifecycleReviewError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_status(raw: str, field_name: str) -> str:
    status = str(raw or "").strip().lower()
    if status not in ALLOWED_STATES:
        raise LifecycleReviewError(f"invalid_status:{field_name}:{status or '<empty>'}")
    return status


def parse_requested_transition(raw: Any) -> Tuple[str, str]:
    if isinstance(raw, str):
        return "", raw.strip().lower()
    if isinstance(raw, dict):
        from_status = str(raw.get("from_status") or raw.get("from") or "").strip().lower()
        to_status = str(
            raw.get("to_status")
            or raw.get("target_status")
            or raw.get("to")
            or raw.get("next_status")
            or ""
        ).strip().lower()
        return from_status, to_status
    raise LifecycleReviewError("requested_transition must be string or object")


def resolve_current_status(
    request: Dict[str, Any],
    target_asset_payload: Dict[str, Any],
    requested_from: str,
) -> str:
    candidates = [
        requested_from,
        request.get("current_status"),
        request.get("from_status"),
        target_asset_payload.get("lifecycle_status"),
        target_asset_payload.get("status"),
        target_asset_payload.get("current_status"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return normalize_status(candidate, "current_status")
    raise LifecycleReviewError("missing_current_status_evidence")


def extract_gate_decision(payload: Dict[str, Any]) -> str:
    for key in ("gate_decision", "final_decision", "verdict", "decision", "status"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return ""


def run_cmd(cmd: List[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(root), check=False, capture_output=True, text=True)


ALLOWED_EVENT_NAMES = {
    "m1.gate.failed",
    "m1.gate.hold",
    "m1.gate.pass",
    "m3.implementation.failed",
    "m3.implementation.completed",
    "m4.lifecycle.transition.approved",
    "m4.lifecycle.transition.rejected",
    "m4.lifecycle.rollback.executed",
    "m5.proposal.rejected",
    "m5.proposal.accepted",
    "asset.health.degraded",
    "asset.health.critical",
}


def validate_domain_event(event_payload: Dict[str, Any]) -> None:
    required = [
        "contract_version",
        "event_id",
        "event_name",
        "event_time",
        "module",
        "trigger_source",
        "severity",
        "evidence_ref",
        "owner_agent_id",
        "dedupe_key",
    ]
    missing = [key for key in required if not str(event_payload.get(key) or "").strip()]
    if missing:
        raise LifecycleReviewError(f"domain_event_missing_fields:{','.join(missing)}")
    if event_payload.get("contract_version") != "0.1.0":
        raise LifecycleReviewError("domain_event_contract_version_invalid")
    if str(event_payload.get("event_name")) not in ALLOWED_EVENT_NAMES:
        raise LifecycleReviewError("domain_event_name_invalid")
    if str(event_payload.get("module")) not in {"m1", "m3", "m4", "m5", "runtime-monitor"}:
        raise LifecycleReviewError("domain_event_module_invalid")
    if str(event_payload.get("trigger_source")) not in {"platform-hook", "domain-hook", "heartbeat", "cron"}:
        raise LifecycleReviewError("domain_event_trigger_source_invalid")
    if str(event_payload.get("severity")) not in {"info", "warning", "critical"}:
        raise LifecycleReviewError("domain_event_severity_invalid")
    if not str(event_payload.get("asset_ref") or event_payload.get("target_product_id") or "").strip():
        raise LifecycleReviewError("domain_event_target_missing")


def emit_domain_event(
    *,
    root: Path,
    event_name: str,
    severity: str,
    evidence_ref: str,
    owner_agent_id: str,
    asset_ref: str,
    reason: str,
) -> str:
    timestamp = now_iso()
    bucket = timestamp[:16].replace("-", "").replace(":", "").replace("T", "T")
    event_id = f"{event_name.replace('.', '-')}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-lifecycle-review"
    payload = {
        "contract_version": "0.1.0",
        "event_id": event_id,
        "event_name": event_name,
        "event_time": timestamp,
        "module": "m4",
        "trigger_source": "domain-hook",
        "severity": severity,
        "asset_ref": asset_ref,
        "evidence_ref": evidence_ref,
        "owner_agent_id": owner_agent_id,
        "dedupe_key": f"{event_name}|{asset_ref}|{bucket}",
        "window_bucket": bucket,
        "trace": {
            "process_id": "lifecycle-review",
            "reason": reason,
        },
    }
    validate_domain_event(payload)
    event_path = root / "runtime_data/evolution/events" / f"{event_id}.json"
    dump_json(event_path, payload)
    return to_rel(event_path, root)


def fail_closed(
    *,
    root: Path,
    output_path: Path,
    runtime_trace_path: Path,
    fail_record_path: Path,
    phase_trace: List[Dict[str, Any]],
    reason: str,
    target_asset_ref: str = "process:lifecycle-review",
) -> int:
    dump_json(
        fail_record_path,
        {
            "timestamp": now_iso(),
            "status": "failed",
            "reason": reason,
            "fail_closed": True,
        },
    )

    dump_json(
        runtime_trace_path,
        {
            "timestamp": now_iso(),
            "process_id": "lifecycle-review",
            "status": "failed",
            "phase_trace": phase_trace,
            "fail_closed_record_ref": to_rel(fail_record_path, root),
            "reason": reason,
        },
    )

    output_payload = {
        "status": "failed",
        "process_id": "lifecycle-review",
        "failure_code": "lifecycle_review_failed",
        "reason": reason,
        "runtime_trace_ref": to_rel(runtime_trace_path, root),
        "fail_closed_record_ref": to_rel(fail_record_path, root),
        "lifecycle_transition_ref": "",
        "registry_sync_ref": "",
        "lifecycle_review_report_ref": "",
    }
    try:
        output_payload["domain_event_ref"] = emit_domain_event(
            root=root,
            event_name="m4.lifecycle.transition.rejected",
            severity="critical",
            evidence_ref=to_rel(runtime_trace_path, root),
            owner_agent_id="hr",
            asset_ref=target_asset_ref,
            reason=reason,
        )
    except Exception:
        pass
    dump_json(output_path, output_payload)
    print(to_rel(output_path, root))
    return 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run lifecycle-review process")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--evidence-dir",
        default="",
        help="Evidence directory path (repo-relative). Default runtime_data/execution/evidence/lifecycle-review/<run_id>",
    )
    parser.add_argument("--run-id", default="", help="Optional run id for evidence directory naming")
    parser.add_argument(
        "--registry-verify-cmd",
        default="python3 shared/registry/registry_contract_tool.py verify",
        help="Registry verification command",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    input_path = resolve_path(root, args.input)
    output_path = resolve_path(root, args.output)
    request = load_json(input_path)

    run_id = args.run_id.strip() or datetime.now(timezone.utc).strftime("lifecycle-review-%Y%m%dT%H%M%SZ")
    evidence_dir = resolve_path(
        root,
        args.evidence_dir.strip() or f"runtime_data/execution/evidence/lifecycle-review/{run_id}",
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    runtime_trace_path = evidence_dir / "runtime_trace.json"
    fail_record_path = evidence_dir / "fail_closed_record.json"
    report_path = evidence_dir / "lifecycle_review_report.json"
    phase_trace: List[Dict[str, Any]] = []

    required = ["final_gate_verdict_ref", "target_asset_ref", "requested_transition"]
    missing = [field for field in required if field not in request]
    if missing:
        return fail_closed(
            root=root,
            output_path=output_path,
            runtime_trace_path=runtime_trace_path,
            fail_record_path=fail_record_path,
            phase_trace=phase_trace,
            reason=f"missing required input fields: {','.join(missing)}",
        )

    try:
        final_gate_verdict_ref = str(request["final_gate_verdict_ref"]).strip()
        target_asset_ref = str(request["target_asset_ref"]).strip()
        requested_transition_raw = request["requested_transition"]
        if not final_gate_verdict_ref or not target_asset_ref:
            raise LifecycleReviewError("required refs must be non-empty strings")

        final_gate_verdict_path = resolve_path(root, final_gate_verdict_ref)
        target_asset_path = resolve_path(root, target_asset_ref)

        # p1: validate-request。先验证输入结构与核心引用可达性。
        if not final_gate_verdict_path.exists():
            raise LifecycleReviewError(f"final_gate_verdict_ref_unreachable:{final_gate_verdict_ref}")
        if not target_asset_path.exists():
            raise LifecycleReviewError(f"target_asset_ref_unreachable:{target_asset_ref}")

        p1_output_path = evidence_dir / "p1_validate_request.json"
        dump_json(
            p1_output_path,
            {
                "timestamp": now_iso(),
                "phase": "validate-request",
                "status": "pass",
                "input_fields": sorted(required),
                "final_gate_verdict_ref": final_gate_verdict_ref,
                "target_asset_ref": target_asset_ref,
            },
        )
        phase_trace.append(
            {
                "phase": "p1-validate-request",
                "status": "pass",
                "output_ref": to_rel(p1_output_path, root),
                "ts": now_iso(),
            }
        )

        # p2: check-prerequisites。验证状态迁移前置条件（当前状态、目标状态、迁移合法性）。
        target_asset_payload = load_json(target_asset_path)
        requested_from, requested_to = parse_requested_transition(requested_transition_raw)
        requested_to_status = normalize_status(requested_to, "requested_transition.to_status")
        current_status = resolve_current_status(request, target_asset_payload, requested_from)

        if requested_from:
            requested_from_status = normalize_status(requested_from, "requested_transition.from_status")
            if requested_from_status != current_status:
                raise LifecycleReviewError(
                    f"from_status_mismatch:requested={requested_from_status},actual={current_status}"
                )

        if requested_to_status == current_status:
            raise LifecycleReviewError("requested_transition_is_noop")
        if requested_to_status not in ALLOWED_TRANSITIONS[current_status]:
            raise LifecycleReviewError(
                f"invalid_lifecycle_transition:{current_status}->{requested_to_status}"
            )

        p2_output_path = evidence_dir / "p2_check_prerequisites.json"
        dump_json(
            p2_output_path,
            {
                "timestamp": now_iso(),
                "phase": "check-prerequisites",
                "status": "pass",
                "current_status": current_status,
                "requested_to_status": requested_to_status,
                "target_asset_ref": target_asset_ref,
            },
        )
        phase_trace.append(
            {
                "phase": "p2-check-prerequisites",
                "status": "pass",
                "current_status": current_status,
                "requested_to_status": requested_to_status,
                "output_ref": to_rel(p2_output_path, root),
                "ts": now_iso(),
            }
        )

        # p3: quality-gate。门禁 verdict 非 pass 时直接 Fail-Closed，禁止执行迁移。
        gate_payload = load_json(final_gate_verdict_path)
        gate_decision = extract_gate_decision(gate_payload)
        if gate_decision not in PASS_DECISIONS:
            raise LifecycleReviewError(f"quality_gate_not_passed:{gate_decision or 'unknown'}")

        p3_output_path = evidence_dir / "p3_quality_gate.json"
        dump_json(
            p3_output_path,
            {
                "timestamp": now_iso(),
                "phase": "quality-gate",
                "status": "pass",
                "gate_decision": gate_decision,
                "final_gate_verdict_ref": final_gate_verdict_ref,
            },
        )
        phase_trace.append(
            {
                "phase": "p3-quality-gate",
                "status": "pass",
                "gate_decision": gate_decision,
                "output_ref": to_rel(p3_output_path, root),
                "ts": now_iso(),
            }
        )

        # p4: execute-transition。仅记录合法迁移结果，不在此脚本内直接修改目标资产。
        lifecycle_transition_path = evidence_dir / "p4_lifecycle_transition.json"
        dump_json(
            lifecycle_transition_path,
            {
                "timestamp": now_iso(),
                "phase": "execute-transition",
                "status": "pass",
                "actor": "hr",
                "target_asset_ref": target_asset_ref,
                "from_status": current_status,
                "to_status": requested_to_status,
                "evidence_refs": [
                    final_gate_verdict_ref,
                    to_rel(p2_output_path, root),
                    to_rel(p3_output_path, root),
                ],
            },
        )
        phase_trace.append(
            {
                "phase": "p4-execute-transition",
                "status": "pass",
                "lifecycle_transition_ref": to_rel(lifecycle_transition_path, root),
                "ts": now_iso(),
            }
        )

        # p5: sync-registry。执行 registry 合约校验，失败则直接 Fail-Closed。
        verify_cmd = shlex.split(args.registry_verify_cmd.strip())
        if not verify_cmd:
            raise LifecycleReviewError("registry_verify_cmd_empty")
        proc = run_cmd(verify_cmd, root)
        verify_stdout_path = evidence_dir / "p5_registry_verify_stdout.log"
        verify_stderr_path = evidence_dir / "p5_registry_verify_stderr.log"
        verify_stdout_path.write_text(proc.stdout, encoding="utf-8")
        verify_stderr_path.write_text(proc.stderr, encoding="utf-8")

        if proc.returncode != 0:
            raise LifecycleReviewError(f"registry_verify_failed:rc={proc.returncode}")

        registry_sync_path = evidence_dir / "p5_registry_sync.json"
        dump_json(
            registry_sync_path,
            {
                "timestamp": now_iso(),
                "phase": "sync-registry",
                "status": "pass",
                "command": verify_cmd,
                "return_code": proc.returncode,
                "stdout_ref": to_rel(verify_stdout_path, root),
                "stderr_ref": to_rel(verify_stderr_path, root),
            },
        )
        phase_trace.append(
            {
                "phase": "p5-sync-registry",
                "status": "pass",
                "registry_sync_ref": to_rel(registry_sync_path, root),
                "ts": now_iso(),
            }
        )

        lifecycle_review_report = {
            "timestamp": now_iso(),
            "process_id": "lifecycle-review",
            "status": "succeeded",
            "target_asset_ref": target_asset_ref,
            "from_status": current_status,
            "to_status": requested_to_status,
            "lifecycle_transition_ref": to_rel(lifecycle_transition_path, root),
            "registry_sync_ref": to_rel(registry_sync_path, root),
            "phase_trace": phase_trace,
        }
        dump_json(report_path, lifecycle_review_report)

        dump_json(
            runtime_trace_path,
            {
                "timestamp": now_iso(),
                "process_id": "lifecycle-review",
                "status": "succeeded",
                "phase_trace": phase_trace,
                "lifecycle_review_report_ref": to_rel(report_path, root),
            },
        )

        domain_event_ref = emit_domain_event(
            root=root,
            event_name="m4.lifecycle.transition.approved",
            severity="info",
            evidence_ref=to_rel(runtime_trace_path, root),
            owner_agent_id="hr",
            asset_ref=target_asset_ref,
            reason=f"{current_status}->{requested_to_status}",
        )

        dump_json(
            output_path,
            {
                "status": "succeeded",
                "process_id": "lifecycle-review",
                "lifecycle_transition_ref": to_rel(lifecycle_transition_path, root),
                "registry_sync_ref": to_rel(registry_sync_path, root),
                "lifecycle_review_report_ref": to_rel(report_path, root),
                "runtime_trace_ref": to_rel(runtime_trace_path, root),
                "domain_event_ref": domain_event_ref,
            },
        )
        print(to_rel(output_path, root))
        return 0

    except LifecycleReviewError as exc:
        return fail_closed(
            root=root,
            output_path=output_path,
            runtime_trace_path=runtime_trace_path,
            fail_record_path=fail_record_path,
            phase_trace=phase_trace,
            reason=str(exc),
            target_asset_ref=str(request.get("target_asset_ref") or "process:lifecycle-review"),
        )


if __name__ == "__main__":
    raise SystemExit(main())
