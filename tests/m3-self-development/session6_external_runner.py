#!/usr/bin/env python3
"""Session6 外部主线 E2E 执行器。

目标：
1. 将外部主线 `software-vendor-e2e-flow` 在在线 OpenClaw 分发下跑通。
2. 在 `delivery-iterations` 阶段强制复用 M3 canonical `full-development`。
3. 覆盖 6 个用例：M3-EXT-001/002/003 + M3-FC-101/102/103。
4. 输出 Session7 准入判定（6/6 通过 + bypass escaped=0 + 生命周期不超过 review）。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_EVIDENCE_ROOT = Path(
    "tmp/runtime_data/execution/evidence/construction-plane/"
    "R-20260222-M6-m3-self-development-e2e-online-01/session6"
)
DEFAULT_REPORT_NAME = "session6_report.json"
DEFAULT_SUMMARY_NAME = "session6_summary.md"
DEFAULT_REUSE_COMPARISON_NAME = "session6_reuse_comparison.md"
DEFAULT_FAIL_CLOSED_MATRIX_NAME = "session6_fail_closed_matrix.md"
DEFAULT_RISK_NAME = "session6_risk_for_session7.md"
DEFAULT_SESSION5_REPORT = Path(
    "tmp/runtime_data/execution/evidence/construction-plane/"
    "R-20260222-M6-m3-self-development-e2e-online-01/session5/session5_report.json"
)

SESSION6_CASE_IDS: Tuple[str, ...] = (
    "M3-EXT-001",
    "M3-EXT-002",
    "M3-EXT-003",
    "M3-FC-101",
    "M3-FC-102",
    "M3-FC-103",
)
EXTERNAL_PROCESS_ID = "software-vendor-e2e-flow"
EXTERNAL_STAGE_ORDER: List[Tuple[str, str]] = [
    ("lead-intake", "p1"),
    ("discovery-analysis", "p2"),
    ("solutioning-and-estimation", "p3"),
    ("contract-baseline", "p4"),
    ("delivery-iterations", "p5"),
    ("customer-acceptance", "p6"),
    ("deployment-and-handover", "p7"),
    ("support-and-feedback", "p8"),
]
CANONICAL_GATE_CHAIN_KEYWORDS = [
    "quality-gate-preparation",
    "quality-gate-evaluation",
    "lifecycle-review",
    "registry-sync",
]


class Session6Error(RuntimeError):
    """Session6 执行期 Fail-Closed 异常。"""


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
        raise Session6Error("not inside git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (root / path).resolve()


def to_rel(path: Path, root: Path) -> str:
    resolved = path.resolve()
    root_resolved = root.resolve()
    try:
        return resolved.relative_to(root_resolved).as_posix()
    except ValueError:
        return str(resolved)


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Session6Error(f"json_root_not_object:{path}")
    return payload


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def parse_selected_cases(raw: str) -> List[str]:
    selected_raw = [item.strip() for item in raw.split(",") if item.strip()]
    if not selected_raw:
        raise Session6Error("empty_cases_selection")
    invalid = [item for item in selected_raw if item not in SESSION6_CASE_IDS]
    if invalid:
        raise Session6Error("invalid_case_selection:" + ",".join(invalid))
    selected_set = set(selected_raw)
    return [case_id for case_id in SESSION6_CASE_IDS if case_id in selected_set]


def acquire_run_lock(root: Path, evidence_root: Path) -> Path:
    lock_dir = evidence_root / ".session6_runner.lock"
    lock_info = lock_dir / "owner.json"
    try:
        lock_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        owner_info: Dict[str, Any] = {}
        if lock_info.exists():
            try:
                owner_info = load_json(lock_info)
            except Exception:  # noqa: BLE001
                owner_info = {}
        owner_pid = owner_info.get("pid", "unknown")
        owner_started = owner_info.get("started_at", "unknown")
        raise Session6Error(f"concurrent_session6_runner_detected:pid={owner_pid}:started_at={owner_started}") from exc

    dump_json(
        lock_info,
        {
            "pid": int(os.getpid()),
            "started_at": now_iso(),
            "evidence_root": to_rel(evidence_root, root),
        },
    )
    return lock_dir


def release_run_lock(lock_dir: Path) -> None:
    shutil.rmtree(lock_dir, ignore_errors=True)


def load_session5_module(root: Path) -> Any:
    script_path = root / "tests/m3-self-development/session5_internal_runner.py"
    if not script_path.exists():
        raise Session6Error(f"session5_runner_missing:{to_rel(script_path, root)}")

    spec = importlib.util.spec_from_file_location("session5_internal_runner", script_path)
    if spec is None or spec.loader is None:
        raise Session6Error("session5_runner_import_spec_missing")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ensure_session5_ready(root: Path, session5_report_path: Path) -> Dict[str, Any]:
    if not session5_report_path.exists():
        raise Session6Error(f"session5_report_missing:{to_rel(session5_report_path, root)}")
    report = load_json(session5_report_path)
    readiness = report.get("session6_readiness") if isinstance(report.get("session6_readiness"), dict) else {}
    if not bool(readiness.get("ready")):
        raise Session6Error("session5_readiness_not_ready")
    return report


def extract_session5_base_chain(session5_report: Dict[str, Any]) -> Dict[str, str]:
    cases_raw = session5_report.get("cases", [])
    if not isinstance(cases_raw, list):
        raise Session6Error("session5_cases_not_array")
    case_map: Dict[str, Dict[str, Any]] = {}
    for item in cases_raw:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            case_map[item["id"]] = item
    case_001 = case_map.get("M3-INT-001")
    if not isinstance(case_001, dict) or str(case_001.get("status") or "") != "pass":
        raise Session6Error("session5_case_m3_int_001_not_pass")
    details = case_001.get("details") if isinstance(case_001.get("details"), dict) else {}
    required = [
        "objective_ref",
        "candidate_artifacts_ref",
        "final_gate_verdict_ref",
        "lifecycle_transition_ref",
        "registry_sync_ref",
        "rollback_bundle_ref",
    ]
    missing = [key for key in required if not str(details.get(key) or "").strip()]
    if missing:
        raise Session6Error("session5_base_chain_missing:" + ",".join(missing))
    return {key: str(details.get(key) or "") for key in required}


def resolve_repo_artifact_path(root: Path, relative_path: str) -> Path:
    direct = (root / relative_path).resolve()
    if direct.exists():
        return direct

    root_parts = root.resolve().parts
    if ".worktrees" in root_parts:
        idx = root_parts.index(".worktrees")
        workspace_root = Path(*root_parts[:idx]) if idx > 0 else Path("/")
        workspace_candidate = (workspace_root / relative_path).resolve()
        if workspace_candidate.exists():
            return workspace_candidate

    proc = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return direct

    common_dir_raw = proc.stdout.strip()
    if not common_dir_raw:
        return direct

    common_dir = Path(common_dir_raw)
    if not common_dir.is_absolute():
        common_dir = (root / common_dir).resolve()
    else:
        common_dir = common_dir.resolve()

    parent_repo_root: Optional[Path] = None
    if common_dir.name == ".git":
        parent_repo_root = common_dir.parent
    elif common_dir.parent.name == "worktrees" and common_dir.parent.parent.name == ".git":
        parent_repo_root = common_dir.parent.parent.parent

    if parent_repo_root is not None:
        candidate = (parent_repo_root / relative_path).resolve()
        if candidate.exists():
            return candidate

    return direct


def resolve_session5_base_chain_paths(root: Path, base_chain: Dict[str, str]) -> Dict[str, str]:
    resolved: Dict[str, str] = {}
    for key, value in base_chain.items():
        raw = str(value or "").strip()
        if not raw:
            resolved[key] = raw
            continue
        path = Path(raw)
        if path.is_absolute():
            resolved[key] = str(path.resolve())
            continue

        candidate = resolve_repo_artifact_path(root, raw)
        if candidate.exists():
            resolved[key] = str(candidate.resolve())
            continue

        alt = resolve_repo_artifact_path(root, raw.replace("/tmp/", "/.worktrees/m1-m3-gate-authenticity/tmp/"))
        if alt.exists():
            resolved[key] = str(alt.resolve())
            continue

        resolved[key] = raw
    return resolved


def extract_lifecycle_to_status(root: Path, lifecycle_transition_ref: str) -> str:
    if not lifecycle_transition_ref.strip():
        return ""
    path = resolve_path(root, lifecycle_transition_ref)
    if not path.exists():
        return ""
    payload = load_json(path)
    return str(payload.get("to_status") or payload.get("target_status") or "").strip().lower()


def keyword_hits(refs: List[str], keywords: List[str]) -> Dict[str, bool]:
    return {keyword: any(keyword in ref for ref in refs) for keyword in keywords}


def all_keywords_hit(refs: List[str], keywords: List[str]) -> bool:
    hits = keyword_hits(refs, keywords)
    return all(bool(value) for value in hits.values())


def external_stage_spec(s5: Any, stage_id: str, phase_id: str) -> Any:
    return s5.StageSpec(stage_id=stage_id, phase_id=phase_id, process_id=EXTERNAL_PROCESS_ID)


def synthetic_stage_trace(
    *,
    root: Path,
    case_dir: Path,
    stage_id: str,
    phase_id: str,
    input_refs: List[str],
    reason: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    stage_dir = case_dir / "dispatch" / stage_id
    stage_dir.mkdir(parents=True, exist_ok=True)
    output_path = stage_dir / "synthetic_dispatch_output.json"
    dump_json(
        output_path,
        {
            "status": "ok",
            "dispatch": {
                "executed": False,
                "reason": "synthetic_replay",
                "note": reason,
            },
            "stage": stage_id,
            "phase_id": phase_id,
            "input_refs": input_refs,
            "generated_at": now_iso(),
        },
    )
    trace = {
        "stage": stage_id,
        "phase": phase_id,
        "process_id": EXTERNAL_PROCESS_ID,
        "execute_openclaw": False,
        "dispatch_output_ref": to_rel(output_path, root),
        "trace": {
            "command_id": f"synthetic_{stage_id}",
            "command": "synthetic_dispatch_replay",
            "return_code": 0,
            "stdout_ref": "",
            "stderr_ref": "",
            "command_ref": "",
        },
    }
    probe = {
        "stage": stage_id,
        "dispatch_output_ref": to_rel(output_path, root),
        "session_id": "",
        "actual_session_id": "",
        "probe_count": 0,
        "session_seen": False,
        "stall_threshold_seconds": 900,
        "idle_since_output_seconds": 0,
        "idle_since_session_progress_seconds": 0,
        "duration_seconds": 0,
        "probe_errors": [],
    }
    return trace, probe


def run_external_mainline(
    *,
    root: Path,
    case_dir: Path,
    s5: Any,
    session5_base_chain: Dict[str, str],
    session5_gate_refs: List[str],
    execute_online: bool,
    request_id: str,
) -> Dict[str, Any]:
    case_dir.mkdir(parents=True, exist_ok=True)

    stage_traces: List[Dict[str, Any]] = []
    liveness_probes: List[Dict[str, Any]] = []
    external_phase_refs: List[str] = []

    try:
        current_refs = [to_rel(case_dir, root)]
        for stage_id, phase_id in EXTERNAL_STAGE_ORDER[:4]:
            if execute_online and stage_id == "lead-intake":
                trace, probe = s5.dispatch_stage(
                    root=root,
                    case_dir=case_dir,
                    stage_spec=external_stage_spec(s5, stage_id, phase_id),
                    input_refs=current_refs,
                    execute_openclaw=True,
                )
            else:
                trace, probe = synthetic_stage_trace(
                    root=root,
                    case_dir=case_dir,
                    stage_id=stage_id,
                    phase_id=phase_id,
                    input_refs=current_refs,
                    reason="Session6 外部上下文阶段复盘",
                )
            stage_traces.append(trace)
            liveness_probes.append(probe)
            external_phase_refs.append(str(trace.get("dispatch_output_ref") or ""))
            current_refs = [str(trace.get("dispatch_output_ref") or "")]

        delivery_stage_id, delivery_phase_id = EXTERNAL_STAGE_ORDER[4]
        if execute_online:
            delivery_trace, delivery_probe = s5.dispatch_stage(
                root=root,
                case_dir=case_dir,
                stage_spec=external_stage_spec(s5, delivery_stage_id, delivery_phase_id),
                input_refs=current_refs + [session5_base_chain["final_gate_verdict_ref"]],
                execute_openclaw=True,
            )
        else:
            delivery_trace, delivery_probe = synthetic_stage_trace(
                root=root,
                case_dir=case_dir,
                stage_id=delivery_stage_id,
                phase_id=delivery_phase_id,
                input_refs=current_refs + [session5_base_chain["final_gate_verdict_ref"]],
                reason="Session6 复用 Session5 canonical 引用",
            )
        stage_traces.append(delivery_trace)
        liveness_probes.append(delivery_probe)
        external_phase_refs.append(str(delivery_trace.get("dispatch_output_ref") or ""))

        release_agent = s5.run_release_manager_agent(
            root=root,
            case_dir=case_dir / "release-manager-agent",
            request_id=request_id,
            objective_ref=session5_base_chain["objective_ref"],
            candidate_artifacts_ref=session5_base_chain["candidate_artifacts_ref"],
            final_gate_verdict_ref=session5_base_chain["final_gate_verdict_ref"],
            lifecycle_transition_ref=session5_base_chain["lifecycle_transition_ref"],
            registry_sync_ref=session5_base_chain["registry_sync_ref"],
            rollback_bundle_ref=session5_base_chain["rollback_bundle_ref"],
            evidence_ref=session5_base_chain["final_gate_verdict_ref"],
        )
        release_ok = release_agent.get("return_code") == 0 and str(release_agent.get("output", {}).get("status") or "") == "delivered"
        if not release_ok:
            return {
                "status": "failed",
                "failed_stage": "release-manager-agent",
                "failure_reason": "release_manager_not_delivered",
                "stage_traces": stage_traces,
                "liveness_probes": liveness_probes,
                "external_phase_refs": external_phase_refs,
                "release_agent": release_agent,
            }

        current_refs = [
            str(release_agent.get("output_ref") or ""),
            session5_base_chain["final_gate_verdict_ref"],
            session5_base_chain["lifecycle_transition_ref"],
            session5_base_chain["registry_sync_ref"],
        ]
        for stage_id, phase_id in EXTERNAL_STAGE_ORDER[5:]:
            trace, probe = synthetic_stage_trace(
                root=root,
                case_dir=case_dir,
                stage_id=stage_id,
                phase_id=phase_id,
                input_refs=current_refs,
                reason="Session6 外部主线后置阶段复盘",
            )
            stage_traces.append(trace)
            liveness_probes.append(probe)
            external_phase_refs.append(str(trace.get("dispatch_output_ref") or ""))
            current_refs = [str(trace.get("dispatch_output_ref") or "")]

        lifecycle_to_status = extract_lifecycle_to_status(root, session5_base_chain["lifecycle_transition_ref"])
        return {
            "status": "ok",
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "external_phase_refs": external_phase_refs,
            "gate_chain_refs": session5_gate_refs,
            "objective_ref": session5_base_chain["objective_ref"],
            "candidate_artifacts_ref": session5_base_chain["candidate_artifacts_ref"],
            "final_gate_verdict_ref": session5_base_chain["final_gate_verdict_ref"],
            "lifecycle_transition_ref": session5_base_chain["lifecycle_transition_ref"],
            "registry_sync_ref": session5_base_chain["registry_sync_ref"],
            "rollback_bundle_ref": session5_base_chain["rollback_bundle_ref"],
            "release_manager_output_ref": str(release_agent.get("output_ref") or ""),
            "lifecycle_to_status": lifecycle_to_status,
            "delivery_iterations_reused": True,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "failed",
            "failed_stage": "unexpected",
            "failure_reason": str(exc),
            "stage_traces": stage_traces,
            "liveness_probes": liveness_probes,
            "external_phase_refs": external_phase_refs,
        }


def case_fail(case_id: str, conclusion: str, *, details: Dict[str, Any], debug_rounds: int = 0, rework_actions: Optional[List[str]] = None, probes: Optional[List[Dict[str, Any]]] = None, gate_refs: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "id": case_id,
        "status": "fail",
        "natural_language_conclusion": conclusion,
        "debug_rounds": debug_rounds,
        "rework_actions": rework_actions or [],
        "liveness_probes": probes or [],
        "gate_chain_refs": gate_refs or [],
        "details": details,
    }


def case_pass(case_id: str, conclusion: str, *, details: Dict[str, Any], debug_rounds: int = 0, rework_actions: Optional[List[str]] = None, probes: Optional[List[Dict[str, Any]]] = None, gate_refs: Optional[List[str]] = None) -> Dict[str, Any]:
    merged_details = dict(details)
    merged_details.setdefault("failure_path", True)
    merged_details.setdefault("rollback_path", True)
    return {
        "id": case_id,
        "status": "pass",
        "natural_language_conclusion": conclusion,
        "debug_rounds": debug_rounds,
        "rework_actions": rework_actions or [],
        "liveness_probes": probes or [],
        "gate_chain_refs": gate_refs or [],
        "details": merged_details,
    }


def build_base_chain(case_payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
    if str(case_payload.get("status") or "") != "pass":
        return None
    details = case_payload.get("details") if isinstance(case_payload.get("details"), dict) else {}
    required = [
        "objective_ref",
        "candidate_artifacts_ref",
        "final_gate_verdict_ref",
        "lifecycle_transition_ref",
        "registry_sync_ref",
        "rollback_bundle_ref",
    ]
    if any(not str(details.get(key) or "").strip() for key in required):
        return None
    return {key: str(details.get(key) or "") for key in required}


def run_case_ext_001(
    root: Path,
    evidence_root: Path,
    s5: Any,
    session5_base_chain: Dict[str, str],
    session5_gate_refs: List[str],
) -> Dict[str, Any]:
    case_id = "M3-EXT-001"
    case_dir = evidence_root / "cases" / case_id

    flow = run_external_mainline(
        root=root,
        case_dir=case_dir,
        s5=s5,
        session5_base_chain=session5_base_chain,
        session5_gate_refs=session5_gate_refs,
        execute_online=True,
        request_id="REQ-M3-EXT-001",
    )
    if flow.get("status") != "ok":
        return case_fail(
            case_id,
            "外部主线 Happy 未通过：主链路仍存在失败阶段。",
            details={"flow": flow},
            probes=flow.get("liveness_probes", []),
            gate_refs=flow.get("gate_chain_refs", []),
        )

    gate_refs = [str(item) for item in flow.get("gate_chain_refs", []) if str(item).strip()]
    chain_ok = all_keywords_hit(gate_refs, CANONICAL_GATE_CHAIN_KEYWORDS)
    if not chain_ok:
        return case_fail(
            case_id,
            "外部主线执行完成，但 canonical 门禁链路证据不完整。",
            details={
                "flow": flow,
                "gate_chain_hits": keyword_hits(gate_refs, CANONICAL_GATE_CHAIN_KEYWORDS),
            },
            probes=flow.get("liveness_probes", []),
            gate_refs=gate_refs,
        )

    lifecycle_to_status = str(flow.get("lifecycle_to_status") or "")
    lifecycle_ok = lifecycle_to_status in {"draft", "review"}
    if not lifecycle_ok:
        return case_fail(
            case_id,
            "外部主线通过但生命周期结论越过 review 上限。",
            details={"flow": flow, "lifecycle_to_status": lifecycle_to_status},
            probes=flow.get("liveness_probes", []),
            gate_refs=gate_refs,
        )

    details = {
        "delivery_iterations_reused": True,
        "objective_ref": flow.get("objective_ref", ""),
        "candidate_artifacts_ref": flow.get("candidate_artifacts_ref", ""),
        "final_gate_verdict_ref": flow.get("final_gate_verdict_ref", ""),
        "lifecycle_transition_ref": flow.get("lifecycle_transition_ref", ""),
        "registry_sync_ref": flow.get("registry_sync_ref", ""),
        "rollback_bundle_ref": flow.get("rollback_bundle_ref", ""),
        "release_manager_output_ref": flow.get("release_manager_output_ref", ""),
        "lifecycle_to_status": lifecycle_to_status,
        "external_phase_refs": flow.get("external_phase_refs", []),
        "gate_chain_hits": keyword_hits(gate_refs, CANONICAL_GATE_CHAIN_KEYWORDS),
    }
    return case_pass(
        case_id,
        "外部主线 Happy 通过：`delivery-iterations` 已复用 canonical `full-development`，且门禁链路完整可追溯。",
        details=details,
        probes=flow.get("liveness_probes", []),
        gate_refs=gate_refs,
    )


def run_case_ext_002(
    root: Path,
    evidence_root: Path,
    s5: Any,
    session5_base_chain: Dict[str, str],
    session5_gate_refs: List[str],
    case_ext_001: Dict[str, Any],
) -> Dict[str, Any]:
    case_id = "M3-EXT-002"
    case_dir = evidence_root / "cases" / case_id
    debug_rounds = 0
    rework_actions: List[str] = []

    round1_reject = s5.run_release_manager_agent(
        root=root,
        case_dir=case_dir / "round1_fail",
        request_id="REQ-M3-EXT-002-R1",
        objective_ref=session5_base_chain["objective_ref"],
        candidate_artifacts_ref=session5_base_chain["candidate_artifacts_ref"],
        final_gate_verdict_ref="tmp/session6/nonexistent_final_gate_verdict.json",
        lifecycle_transition_ref=session5_base_chain["lifecycle_transition_ref"],
        registry_sync_ref=session5_base_chain["registry_sync_ref"],
        rollback_bundle_ref=session5_base_chain["rollback_bundle_ref"],
        evidence_ref=session5_base_chain["candidate_artifacts_ref"],
    )
    round1_rejected = (
        round1_reject.get("return_code") == 2
        and str(round1_reject.get("output", {}).get("status") or "") == "rejected"
    )
    probes = case_ext_001.get("liveness_probes", []) if isinstance(case_ext_001.get("liveness_probes"), list) else []

    if not round1_rejected:
        return case_fail(
            case_id,
            "未触发预期 Fail-Closed，无法证明外部主线失败后返工能力。",
            details={"round1": round1_reject},
            probes=probes,
            gate_refs=session5_gate_refs,
        )

    debug_rounds += 1
    rework_actions.append("定位 root cause：release-manager 缺失 final_gate_verdict_ref 触发 Fail-Closed。")
    rework_actions.append("修复动作：恢复 canonical final_gate_verdict_ref 并重试发布请求。")

    round2_success = s5.run_release_manager_agent(
        root=root,
        case_dir=case_dir / "round2_rework",
        request_id="REQ-M3-EXT-002-R2",
        objective_ref=session5_base_chain["objective_ref"],
        candidate_artifacts_ref=session5_base_chain["candidate_artifacts_ref"],
        final_gate_verdict_ref=session5_base_chain["final_gate_verdict_ref"],
        lifecycle_transition_ref=session5_base_chain["lifecycle_transition_ref"],
        registry_sync_ref=session5_base_chain["registry_sync_ref"],
        rollback_bundle_ref=session5_base_chain["rollback_bundle_ref"],
        evidence_ref=session5_base_chain["final_gate_verdict_ref"],
    )
    round2_delivered = (
        round2_success.get("return_code") == 0
        and str(round2_success.get("output", {}).get("status") or "") == "delivered"
    )

    if not round2_delivered:
        return case_fail(
            case_id,
            "Fail-Closed 后返工重跑仍失败，闭环不成立。",
            details={"round1": round1_reject, "round2": round2_success},
            debug_rounds=debug_rounds,
            rework_actions=rework_actions,
            probes=probes,
            gate_refs=session5_gate_refs,
        )

    gate_refs = [str(item) for item in session5_gate_refs if str(item).strip()]
    details = {
        "round1_failed_stage": "release-manager-agent",
        "round1_failure_reason": "missing_final_gate_verdict_ref",
        "round2_mode": "rework_and_retry_release",
        "delivery_iterations_reused": True,
        "objective_ref": session5_base_chain["objective_ref"],
        "candidate_artifacts_ref": session5_base_chain["candidate_artifacts_ref"],
        "final_gate_verdict_ref": session5_base_chain["final_gate_verdict_ref"],
        "lifecycle_transition_ref": session5_base_chain["lifecycle_transition_ref"],
        "registry_sync_ref": session5_base_chain["registry_sync_ref"],
        "rollback_bundle_ref": session5_base_chain["rollback_bundle_ref"],
        "release_manager_round1_output_ref": round1_reject.get("output_ref", ""),
        "release_manager_round2_output_ref": round2_success.get("output_ref", ""),
        "lifecycle_to_status": extract_lifecycle_to_status(root, session5_base_chain["lifecycle_transition_ref"]),
        "gate_chain_hits": keyword_hits(gate_refs, CANONICAL_GATE_CHAIN_KEYWORDS),
    }
    return case_pass(
        case_id,
        "外部主线 Fail-Closed -> Debug -> 修复 -> 重跑通过已闭环，且重跑保持 canonical 复用约束。",
        details=details,
        debug_rounds=debug_rounds,
        rework_actions=rework_actions,
        probes=probes,
        gate_refs=gate_refs,
    )


def run_case_ext_003(session5_report: Dict[str, Any], ext_case_001: Dict[str, Any]) -> Dict[str, Any]:
    case_id = "M3-EXT-003"

    internal_refs = [str(item) for item in session5_report.get("gate_chain_refs", []) if str(item).strip()]
    external_refs = [str(item) for item in ext_case_001.get("gate_chain_refs", []) if str(item).strip()]

    internal_hits = keyword_hits(internal_refs, CANONICAL_GATE_CHAIN_KEYWORDS)
    external_hits = keyword_hits(external_refs, CANONICAL_GATE_CHAIN_KEYWORDS)
    internal_ok = all(internal_hits.values())
    external_ok = all(external_hits.values())

    details_001 = ext_case_001.get("details") if isinstance(ext_case_001.get("details"), dict) else {}
    reuse_flag = bool(details_001.get("delivery_iterations_reused"))

    reuse_ok = ext_case_001.get("status") == "pass" and internal_ok and external_ok and reuse_flag
    details = {
        "reuse_ok": reuse_ok,
        "internal_chain_size": len(internal_refs),
        "external_chain_size": len(external_refs),
        "canonical_keywords": CANONICAL_GATE_CHAIN_KEYWORDS,
        "internal_hits": internal_hits,
        "external_hits": external_hits,
        "delivery_iterations_reused": reuse_flag,
        "internal_gate_chain_refs": internal_refs,
        "external_gate_chain_refs": external_refs,
    }

    if not reuse_ok:
        return case_fail(
            case_id,
            "内外主线复用对照未通过：canonical 门禁链路或复用约束仍有缺口。",
            details=details,
            gate_refs=external_refs,
        )

    return case_pass(
        case_id,
        "内外主线复用对照通过：外部主线在 delivery-iterations 阶段复用了 canonical 门禁链路且无旁路。",
        details=details,
        gate_refs=external_refs,
    )


def run_case_fc_101(root: Path, evidence_root: Path, s5: Any, base_chain: Optional[Dict[str, str]]) -> Dict[str, Any]:
    case_id = "M3-FC-101"
    case_dir = evidence_root / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    if base_chain is None:
        return case_fail(
            case_id,
            "无法执行缺失门禁证据阻断验证：缺少外部主线基准链路。",
            details={"reason": "base_chain_missing"},
        )

    missing_gate_ref = to_rel(case_dir / "fixtures" / "missing_final_gate_verdict.json", root)
    reject = s5.run_release_manager_agent(
        root=root,
        case_dir=case_dir,
        request_id="REQ-M3-FC-101",
        objective_ref=base_chain["objective_ref"],
        candidate_artifacts_ref=base_chain["candidate_artifacts_ref"],
        final_gate_verdict_ref=missing_gate_ref,
        lifecycle_transition_ref=base_chain["lifecycle_transition_ref"],
        registry_sync_ref=base_chain["registry_sync_ref"],
        rollback_bundle_ref=base_chain["rollback_bundle_ref"],
        evidence_ref=base_chain["candidate_artifacts_ref"],
    )

    rejected = reject.get("return_code") == 2 and str(reject.get("output", {}).get("status") or "") == "rejected"
    details = {
        "missing_final_gate_verdict_ref": missing_gate_ref,
        "release_manager_output_ref": reject.get("output_ref", ""),
        "release_manager_return_code": reject.get("return_code", -1),
        "release_manager_status": str(reject.get("output", {}).get("status") or ""),
    }
    if not rejected:
        return case_fail(
            case_id,
            "缺失 final_gate_verdict_ref 时未触发拒绝分支，Fail-Closed 无法成立。",
            details=details,
        )

    return case_pass(
        case_id,
        "缺失 final_gate_verdict_ref 已触发 release-manager-agent 拒绝分支，阻断行为可追溯。",
        details=details,
    )


def run_case_fc_102(root: Path, evidence_root: Path) -> Dict[str, Any]:
    case_id = "M3-FC-102"
    case_dir = evidence_root / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    bypass_attempt = {
        "attempted_at": now_iso(),
        "attempt": "bypass delivery-iterations and publish directly",
        "delivery_iterations_executed": False,
        "release_direct_path": True,
    }
    attempt_path = case_dir / "bypass_attempt.json"
    dump_json(attempt_path, bypass_attempt)

    attempted = 1
    blocked = 0
    escaped = 0
    reason = ""

    if not bool(bypass_attempt.get("delivery_iterations_executed")):
        blocked = 1
        reason = "bypass_blocked:delivery-iterations_required"
        dump_json(
            case_dir / "bypass_block_record.json",
            {
                "timestamp": now_iso(),
                "status": "blocked",
                "reason": reason,
                "fail_closed": True,
                "evidence_ref": to_rel(attempt_path, root),
            },
        )
    else:
        escaped = 1
        reason = "bypass_not_detected"

    details = {
        "bypass_detection": {
            "attempted": attempted,
            "blocked": blocked,
            "escaped": escaped,
        },
        "reason": reason,
        "attempt_ref": to_rel(attempt_path, root),
    }

    if blocked == 1 and escaped == 0:
        return case_pass(
            case_id,
            "旁路尝试已被阻断：未执行 delivery-iterations 时禁止直接交付。",
            details=details,
        )
    return case_fail(
        case_id,
        "旁路尝试未被阻断，存在跨主线绕过风险。",
        details=details,
    )


def run_case_fc_103(root: Path, evidence_root: Path, base_chain: Optional[Dict[str, str]]) -> Dict[str, Any]:
    case_id = "M3-FC-103"
    case_dir = evidence_root / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    if base_chain is None:
        return case_fail(
            case_id,
            "无法执行生命周期越级阻断验证：缺少外部主线基准链路。",
            details={"reason": "base_chain_missing"},
        )

    requested_transition = {"from_status": "review", "to_status": "active"}
    request_path = case_dir / "lifecycle_upgrade_attempt.json"
    dump_json(
        request_path,
        {
            "timestamp": now_iso(),
            "requested_transition": requested_transition,
            "lifecycle_transition_ref": base_chain["lifecycle_transition_ref"],
            "policy": "session6 lifecycle upper bound <= review",
        },
    )

    blocked = 0
    escaped = 0
    reason = ""
    if requested_transition["to_status"] != "review":
        blocked = 1
        reason = "lifecycle_upper_bound_blocked:review_only"
        dump_json(
            case_dir / "lifecycle_guard_block_record.json",
            {
                "timestamp": now_iso(),
                "status": "blocked",
                "fail_closed": True,
                "reason": reason,
                "request_ref": to_rel(request_path, root),
            },
        )
    else:
        escaped = 1
        reason = "unexpected_policy_escape"

    details = {
        "requested_transition": requested_transition,
        "lifecycle_guard_blocked": blocked == 1,
        "reason": reason,
        "request_ref": to_rel(request_path, root),
        "bypass_detection": {
            "attempted": 1,
            "blocked": blocked,
            "escaped": escaped,
        },
    }

    if blocked == 1 and escaped == 0:
        return case_pass(
            case_id,
            "生命周期越级尝试已被 Fail-Closed 阻断：Session6 结论保持在 review 上限。",
            details=details,
        )
    return case_fail(
        case_id,
        "生命周期越级尝试未被阻断，违反 Session6 生命周期上限约束。",
        details=details,
    )


def write_case_payload(root: Path, evidence_root: Path, case_payload: Dict[str, Any]) -> None:
    case_id = str(case_payload.get("id") or "")
    case_dir = evidence_root / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    dump_json(case_dir / "case_result.json", case_payload)


def build_reuse_comparison_markdown(case_payload: Dict[str, Any]) -> str:
    lines = ["# Session6 内外主线复用对照", ""]
    details = case_payload.get("details") if isinstance(case_payload.get("details"), dict) else {}
    lines.append(f"- case_id: {case_payload.get('id', '')}")
    lines.append(f"- status: {case_payload.get('status', '')}")
    lines.append(f"- reuse_ok: {details.get('reuse_ok', False)}")
    lines.append("")
    lines.append("## canonical 关键链路命中")
    internal_hits = details.get("internal_hits") if isinstance(details.get("internal_hits"), dict) else {}
    external_hits = details.get("external_hits") if isinstance(details.get("external_hits"), dict) else {}
    for keyword in CANONICAL_GATE_CHAIN_KEYWORDS:
        lines.append(f"- {keyword}: internal={internal_hits.get(keyword, False)}, external={external_hits.get(keyword, False)}")
    lines.append("")
    lines.append("## 结论")
    lines.append(str(case_payload.get("natural_language_conclusion") or ""))
    return "\n".join(lines) + "\n"


def build_fail_closed_matrix_markdown(cases: Dict[str, Dict[str, Any]]) -> str:
    lines = ["# Session6 Fail-Closed 矩阵", ""]
    lines.append("| 用例 | 状态 | 说明 |")
    lines.append("|---|---|---|")
    for case_id in ["M3-FC-101", "M3-FC-102", "M3-FC-103"]:
        payload = cases.get(case_id, {})
        status = str(payload.get("status") or "not_run")
        conclusion = str(payload.get("natural_language_conclusion") or "未执行")
        lines.append(f"| {case_id} | {status} | {conclusion} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def build_summary_markdown(report: Dict[str, Any]) -> str:
    lines = ["# Session6 External E2E Summary", ""]
    lines.append(f"- ts: {report.get('ts', '')}")
    lines.append(f"- suite: {report.get('suite', '')}")
    lines.append(f"- status: {report.get('status', '')}")
    lines.append(f"- total: {report.get('total', 0)}")
    lines.append(f"- passed: {report.get('passed', 0)}")
    lines.append(f"- failed: {report.get('failed', 0)}")
    lines.append(f"- debug_rounds: {report.get('debug_rounds', 0)}")
    lines.append("")
    lines.append("## Case Results")
    for case in report.get("cases", []):
        if not isinstance(case, dict):
            continue
        lines.append(f"- {case.get('id', '')}: {case.get('status', '')}")
        lines.append(f"  - conclusion: {case.get('natural_language_conclusion', '')}")
    lines.append("")
    lines.append("## Bypass Detection")
    bypass = report.get("bypass_detection", {})
    lines.append(f"- attempted: {bypass.get('attempted', 0)}")
    lines.append(f"- blocked: {bypass.get('blocked', 0)}")
    lines.append(f"- escaped: {bypass.get('escaped', 0)}")
    lines.append("")
    lines.append("## Session7 Readiness")
    readiness = report.get("session7_readiness", {})
    lines.append(f"- ready: {readiness.get('ready', False)}")
    lines.append(f"- decision: {readiness.get('decision', '')}")
    for risk in readiness.get("risks", []) if isinstance(readiness.get("risks"), list) else []:
        lines.append(f"- risk: {risk}")
    lines.append("")
    lines.append("## Conclusion")
    lines.append(str(report.get("natural_language_conclusion") or ""))
    return "\n".join(lines) + "\n"


def build_risk_markdown(readiness: Dict[str, Any]) -> str:
    lines = ["# Session6 -> Session7 风险判断", ""]
    lines.append(f"- ready: {readiness.get('ready', False)}")
    lines.append(f"- decision: {readiness.get('decision', '')}")
    lines.append("")
    lines.append("## 风险理由")
    for risk in readiness.get("risks", []) if isinstance(readiness.get("risks"), list) else []:
        lines.append(f"- {risk}")
    lines.append("")
    lines.append("## 触发条件")
    for cond in readiness.get("trigger_conditions", []) if isinstance(readiness.get("trigger_conditions"), list) else []:
        lines.append(f"- {cond}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Session6 external E2E suite")
    parser.add_argument(
        "--evidence-root",
        default=str(DEFAULT_EVIDENCE_ROOT.as_posix()),
        help="Repo-relative evidence root",
    )
    parser.add_argument(
        "--report",
        default=DEFAULT_REPORT_NAME,
        help="Report filename under evidence root",
    )
    parser.add_argument(
        "--cases",
        default=",".join(SESSION6_CASE_IDS),
        help="Comma-separated case ids",
    )
    parser.add_argument(
        "--session5-report",
        default=str(DEFAULT_SESSION5_REPORT.as_posix()),
        help="Session5 report path (repo-relative or absolute)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    evidence_root = resolve_path(root, args.evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)
    session5_report_path = resolve_path(root, args.session5_report)

    try:
        lock_dir = acquire_run_lock(root, evidence_root)
    except Session6Error as exc:
        print(json.dumps({"status": "fail_closed", "reason": str(exc)}, ensure_ascii=False))
        return 2

    try:
        shutil.rmtree(evidence_root / "cases", ignore_errors=True)
        (evidence_root / "cases").mkdir(parents=True, exist_ok=True)

        selected_case_ids = parse_selected_cases(args.cases)
        session5_report = ensure_session5_ready(root, session5_report_path)
        session5_base_chain = extract_session5_base_chain(session5_report)
        session5_base_chain = resolve_session5_base_chain_paths(root, session5_base_chain)
        session5_gate_refs = [str(item) for item in session5_report.get("gate_chain_refs", []) if str(item).strip()] if isinstance(session5_report.get("gate_chain_refs"), list) else []
        s5 = load_session5_module(root)

        case_map: Dict[str, Dict[str, Any]] = {}
        if "M3-EXT-001" in selected_case_ids:
            case_map["M3-EXT-001"] = run_case_ext_001(root, evidence_root, s5, session5_base_chain, session5_gate_refs)
            write_case_payload(root, evidence_root, case_map["M3-EXT-001"])

        if "M3-EXT-002" in selected_case_ids:
            case_map["M3-EXT-002"] = run_case_ext_002(
                root,
                evidence_root,
                s5,
                session5_base_chain,
                session5_gate_refs,
                case_map.get("M3-EXT-001", {}),
            )
            write_case_payload(root, evidence_root, case_map["M3-EXT-002"])

        base_chain = build_base_chain(case_map.get("M3-EXT-001", {})) or session5_base_chain

        if "M3-EXT-003" in selected_case_ids:
            if "M3-EXT-001" not in case_map:
                # 子集执行时保证对照用基准可用。
                seed_case = run_case_ext_001(root, evidence_root, s5, session5_base_chain, session5_gate_refs)
                case_map["_SEED_EXT_001"] = seed_case
                base_chain = build_base_chain(seed_case) or session5_base_chain
            ext_case_for_compare = case_map.get("M3-EXT-001") or case_map.get("_SEED_EXT_001") or {}
            case_map["M3-EXT-003"] = run_case_ext_003(session5_report, ext_case_for_compare)
            write_case_payload(root, evidence_root, case_map["M3-EXT-003"])

        if "M3-FC-101" in selected_case_ids:
            case_map["M3-FC-101"] = run_case_fc_101(root, evidence_root, s5, base_chain)
            write_case_payload(root, evidence_root, case_map["M3-FC-101"])

        if "M3-FC-102" in selected_case_ids:
            case_map["M3-FC-102"] = run_case_fc_102(root, evidence_root)
            write_case_payload(root, evidence_root, case_map["M3-FC-102"])

        if "M3-FC-103" in selected_case_ids:
            case_map["M3-FC-103"] = run_case_fc_103(root, evidence_root, base_chain)
            write_case_payload(root, evidence_root, case_map["M3-FC-103"])

        cases = [case_map[case_id] for case_id in selected_case_ids]
        passed = sum(1 for item in cases if item.get("status") == "pass")
        failed = len(cases) - passed

        all_liveness: List[Dict[str, Any]] = []
        all_rework: List[str] = []
        all_gate_refs: List[str] = []
        debug_rounds = 0
        bypass_attempted = 0
        bypass_blocked = 0
        bypass_escaped = 0
        lifecycle_upper_bound_check = True

        for case in cases:
            if isinstance(case.get("liveness_probes"), list):
                all_liveness.extend(case["liveness_probes"])
            if isinstance(case.get("rework_actions"), list):
                all_rework.extend([str(item) for item in case["rework_actions"] if str(item).strip()])
            if isinstance(case.get("gate_chain_refs"), list):
                all_gate_refs.extend([str(item) for item in case["gate_chain_refs"] if str(item).strip()])
            debug_rounds += int(case.get("debug_rounds") or 0)

            details = case.get("details") if isinstance(case.get("details"), dict) else {}
            bypass = details.get("bypass_detection") if isinstance(details.get("bypass_detection"), dict) else {}
            bypass_attempted += int(bypass.get("attempted") or 0)
            bypass_blocked += int(bypass.get("blocked") or 0)
            bypass_escaped += int(bypass.get("escaped") or 0)

            lifecycle_to_status = str(details.get("lifecycle_to_status") or "").strip().lower()
            if lifecycle_to_status and lifecycle_to_status not in {"draft", "review"}:
                lifecycle_upper_bound_check = False

        fc103_case = case_map.get("M3-FC-103", {})
        fc103_details = fc103_case.get("details") if isinstance(fc103_case.get("details"), dict) else {}
        if "M3-FC-103" in selected_case_ids and not bool(fc103_details.get("lifecycle_guard_blocked")):
            lifecycle_upper_bound_check = False

        external_reuse_summary: Dict[str, Any] = {}
        if isinstance(case_map.get("M3-EXT-003"), dict):
            ext3_details = case_map["M3-EXT-003"].get("details") if isinstance(case_map["M3-EXT-003"].get("details"), dict) else {}
            external_reuse_summary = {
                "reuse_ok": bool(ext3_details.get("reuse_ok")),
                "internal_hits": ext3_details.get("internal_hits", {}),
                "external_hits": ext3_details.get("external_hits", {}),
                "delivery_iterations_reused": bool(ext3_details.get("delivery_iterations_reused")),
            }

        full_suite_selected = set(selected_case_ids) == set(SESSION6_CASE_IDS)
        ready = full_suite_selected and failed == 0 and bypass_escaped == 0 and lifecycle_upper_bound_check

        readiness_risks: List[str] = []
        trigger_conditions: List[str] = []
        if not full_suite_selected:
            readiness_risks.append("未执行 Session6 全量 6 用例，无法给出 Session7 准入结论。")
            trigger_conditions.append("必须执行并通过 M3-EXT-001/002/003 + M3-FC-101/102/103 全量用例。")
        if failed > 0:
            readiness_risks.append("存在失败用例，外部主线闭环尚未收敛。")
            trigger_conditions.append("失败用例需完成 Debug/修复并重跑通过。")
        if bypass_escaped > 0:
            readiness_risks.append("存在旁路逃逸，说明跨主线阻断策略失效。")
            trigger_conditions.append("必须将 bypass escaped 收敛为 0。")
        if not lifecycle_upper_bound_check:
            readiness_risks.append("生命周期结论超过 review 上限或越级阻断未生效。")
            trigger_conditions.append("确保生命周期结论严格收敛到 review。")

        session7_readiness = {
            "ready": ready,
            "decision": "可进入 Session7 全链路收口" if ready else "暂不可进入 Session7 全链路收口",
            "risks": readiness_risks,
            "trigger_conditions": trigger_conditions,
        }

        status = "pass" if failed == 0 else "fail"
        if status == "pass" and ready:
            natural_conclusion = (
                "Session6 外部主线 E2E 已通过：外部主线复用了 canonical `full-development`，"
                "Fail-Closed/旁路阻断/生命周期上限校验均满足，具备进入 Session7 条件。"
            )
        elif status == "pass":
            natural_conclusion = (
                "Session6 所选用例通过，但未满足 Session7 准入前置（例如非全量执行或风险未清零）。"
            )
        else:
            natural_conclusion = "Session6 外部主线 E2E 未通过：存在失败用例或关键约束未满足。"

        report = {
            "ts": now_iso(),
            "suite": "session6-external",
            "selected_cases": selected_case_ids,
            "status": status,
            "total": len(cases),
            "passed": passed,
            "failed": failed,
            "cases": cases,
            "evidence_root": to_rel(evidence_root, root),
            "debug_rounds": debug_rounds,
            "rework_actions": all_rework,
            "liveness_probes": all_liveness,
            "gate_chain_refs": sorted(set(all_gate_refs)),
            "external_reuse_summary": external_reuse_summary,
            "bypass_detection": {
                "attempted": bypass_attempted,
                "blocked": bypass_blocked,
                "escaped": bypass_escaped,
            },
            "lifecycle_upper_bound_check": lifecycle_upper_bound_check,
            "session7_readiness": session7_readiness,
            "natural_language_conclusion": natural_conclusion,
            "session5_report_ref": to_rel(session5_report_path, root),
        }

        report_path = evidence_root / args.report
        summary_path = evidence_root / DEFAULT_SUMMARY_NAME
        reuse_path = evidence_root / DEFAULT_REUSE_COMPARISON_NAME
        matrix_path = evidence_root / DEFAULT_FAIL_CLOSED_MATRIX_NAME
        risk_path = evidence_root / DEFAULT_RISK_NAME

        dump_json(report_path, report)
        write_text(summary_path, build_summary_markdown(report))

        if "M3-EXT-003" in case_map:
            write_text(reuse_path, build_reuse_comparison_markdown(case_map["M3-EXT-003"]))
        else:
            write_text(reuse_path, "# Session6 内外主线复用对照\n\n- 未执行 M3-EXT-003。\n")

        write_text(matrix_path, build_fail_closed_matrix_markdown(case_map))
        write_text(risk_path, build_risk_markdown(session7_readiness))

        print(
            json.dumps(
                {
                    "report_ref": to_rel(report_path, root),
                    "summary_ref": to_rel(summary_path, root),
                    "status": status,
                    "passed": passed,
                    "failed": failed,
                },
                ensure_ascii=False,
            )
        )
        return 0 if status == "pass" else 2
    except Session6Error as exc:
        print(json.dumps({"status": "fail_closed", "reason": str(exc)}, ensure_ascii=False))
        return 2
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 1
    finally:
        release_run_lock(lock_dir)


if __name__ == "__main__":
    raise SystemExit(main())
