#!/usr/bin/env python3
"""M5 运行态实例积压止血工具。

职责：
1. 生成实例池基线快照（状态/阶段分布、时间窗口、样本）。
2. 对满足“running+p1+超阈值+dispatch.executed=false”的实例执行受控收敛。

Fail-Closed：
- 候选实例结构不满足最小约束时直接失败，不写入任何实例。
- 报告与 touched 清单始终落盘，便于审计。
"""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_INSTANCE_ROOTS = [
    "agents/control/BPM/memory/process_instances",
    "tmp/m2-bpm-runtime/trigger-runtime-sandbox/instances",
]
DEFAULT_DISPATCH_GLOB = "runtime_data/execution/evidence/m5-self-evolution/hook-bridge/**/p3_dispatch_output.json"


class TriageError(RuntimeError):
    """Fail-closed triage error."""


@dataclass
class InstanceRecord:
    instance_id: str
    status: str
    current_phase: str
    updated_at: str
    age_seconds: int | None
    pool_root: Path
    context_path: Path
    context: Dict[str, Any]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime(ISO_FMT)


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise TriageError("not inside a git repository")
    return Path(proc.stdout.strip()).resolve()


def resolve_path(root: Path, raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate.resolve()
    return (root / candidate).resolve()


def to_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TriageError(f"missing_file:{path}") from exc
    except json.JSONDecodeError as exc:
        raise TriageError(f"invalid_json:{path}:{exc}") from exc
    if not isinstance(payload, dict):
        raise TriageError(f"json_root_not_object:{path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_iso(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    try:
        return datetime.strptime(text, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def expand_dispatch_paths(root: Path, raw_glob: str) -> List[Path]:
    pattern = raw_glob if Path(raw_glob).is_absolute() else str((root / raw_glob).resolve())
    files = [Path(item).resolve() for item in glob.glob(pattern, recursive=True)]
    return sorted([item for item in files if item.is_file()])


def load_dispatch_index(root: Path, raw_glob: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    paths = expand_dispatch_paths(root, raw_glob)
    by_instance: Dict[str, Dict[str, Any]] = {}

    parse_errors: List[str] = []
    executed_true = 0
    executed_false = 0
    executed_unknown = 0

    for path in paths:
        try:
            payload = load_json(path)
        except TriageError as exc:
            parse_errors.append(str(exc))
            continue

        instance_id = str(payload.get("instance_id") or "").strip()
        if not instance_id:
            parse_errors.append(f"missing_instance_id:{to_rel(path, root)}")
            continue

        dispatch = payload.get("dispatch") if isinstance(payload.get("dispatch"), dict) else {}
        executed_raw = dispatch.get("executed")
        executed: bool | None
        if isinstance(executed_raw, bool):
            executed = executed_raw
            if executed:
                executed_true += 1
            else:
                executed_false += 1
        else:
            executed = None
            executed_unknown += 1

        mtime = path.stat().st_mtime
        prev = by_instance.get(instance_id)
        # 同一实例保留最新证据，避免旧记录覆盖当前状态。
        if prev is None or float(prev.get("mtime", 0.0)) <= mtime:
            by_instance[instance_id] = {
                "instance_id": instance_id,
                "executed": executed,
                "dispatch_ref": to_rel(path, root),
                "mtime": mtime,
            }

    summary = {
        "dispatch_glob": raw_glob,
        "total_files": len(paths),
        "mapped_instances": len(by_instance),
        "executed_true_files": executed_true,
        "executed_false_files": executed_false,
        "executed_unknown_files": executed_unknown,
        "parse_error_count": len(parse_errors),
        "parse_errors": parse_errors[:20],
    }
    return by_instance, summary


def collect_instances(root: Path, instance_roots: List[Path], sample_size: int) -> Tuple[List[InstanceRecord], Dict[str, Any], List[str]]:
    now = datetime.now(timezone.utc)
    records: List[InstanceRecord] = []
    scan_errors: List[str] = []
    pool_summaries: List[Dict[str, Any]] = []

    running_phase_distribution: Dict[str, int] = {}
    status_distribution: Dict[str, int] = {}

    oldest_updated: datetime | None = None
    newest_updated: datetime | None = None
    sample_running_p1: List[Dict[str, Any]] = []

    for pool_root in instance_roots:
        contexts = sorted(pool_root.glob("*/context.json"))
        pool_total = 0
        pool_status: Dict[str, int] = {}
        pool_running_phase: Dict[str, int] = {}

        for context_path in contexts:
            pool_total += 1
            try:
                context = load_json(context_path)
            except TriageError as exc:
                scan_errors.append(str(exc))
                continue

            instance_id = str(context.get("instance_id") or context_path.parent.name).strip() or context_path.parent.name
            status = str(context.get("status") or "").strip().lower()
            current_phase = str(context.get("current_phase") or "").strip()
            updated_at = str(context.get("updated_at") or "")
            updated_dt = parse_iso(updated_at)
            age_seconds = None if updated_dt is None else int((now - updated_dt).total_seconds())

            if updated_dt is not None:
                oldest_updated = updated_dt if oldest_updated is None or updated_dt < oldest_updated else oldest_updated
                newest_updated = updated_dt if newest_updated is None or updated_dt > newest_updated else newest_updated

            status_distribution[status] = status_distribution.get(status, 0) + 1
            pool_status[status] = pool_status.get(status, 0) + 1

            if status == "running":
                running_phase_distribution[current_phase] = running_phase_distribution.get(current_phase, 0) + 1
                pool_running_phase[current_phase] = pool_running_phase.get(current_phase, 0) + 1

            if status == "running" and current_phase == "p1" and len(sample_running_p1) < sample_size:
                sample_running_p1.append(
                    {
                        "instance_id": instance_id,
                        "updated_at": updated_at,
                        "age_seconds": age_seconds,
                        "pool": to_rel(pool_root, root),
                        "context_ref": to_rel(context_path, root),
                    }
                )

            records.append(
                InstanceRecord(
                    instance_id=instance_id,
                    status=status,
                    current_phase=current_phase,
                    updated_at=updated_at,
                    age_seconds=age_seconds,
                    pool_root=pool_root,
                    context_path=context_path,
                    context=context,
                )
            )

        pool_summaries.append(
            {
                "pool_root": to_rel(pool_root, root),
                "total_context_files": pool_total,
                "status_distribution": pool_status,
                "running_phase_distribution": pool_running_phase,
            }
        )

    summary = {
        "total_instances": len(records),
        "status_distribution": status_distribution,
        "running_phase_distribution": running_phase_distribution,
        "oldest_updated_at": oldest_updated.strftime(ISO_FMT) if oldest_updated else "",
        "newest_updated_at": newest_updated.strftime(ISO_FMT) if newest_updated else "",
        "pools": pool_summaries,
        "sample_running_p1": sample_running_p1,
        "scan_error_count": len(scan_errors),
        "scan_errors": scan_errors[:20],
    }
    return records, summary, scan_errors


def choose_candidates(
    *,
    records: List[InstanceRecord],
    dispatch_index: Dict[str, Dict[str, Any]],
    age_threshold_seconds: int,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    candidates: List[Dict[str, Any]] = []
    errors: List[str] = []

    for record in records:
        if record.status != "running":
            continue
        if record.current_phase != "p1":
            continue
        if record.age_seconds is None or record.age_seconds < age_threshold_seconds:
            continue

        dispatch = dispatch_index.get(record.instance_id)
        if dispatch is None:
            continue
        if dispatch.get("executed") is not False:
            continue

        phase_results = record.context.get("phase_results")
        if not isinstance(phase_results, list) or not phase_results:
            errors.append(f"invalid_candidate_context:{record.instance_id}:phase_results_not_list")
            continue
        tail = phase_results[-1]
        if not isinstance(tail, dict):
            errors.append(f"invalid_candidate_context:{record.instance_id}:phase_result_tail_not_object")
            continue
        if not isinstance(record.context.get("updated_at"), str) or not parse_iso(record.context.get("updated_at")):
            errors.append(f"invalid_candidate_context:{record.instance_id}:updated_at_invalid")
            continue

        triage_history = record.context.get("triage_history")
        if triage_history is not None and not isinstance(triage_history, list):
            errors.append(f"invalid_candidate_context:{record.instance_id}:triage_history_not_list")
            continue

        candidates.append(
            {
                "instance_id": record.instance_id,
                "age_seconds": record.age_seconds,
                "context_path": record.context_path,
                "context": record.context,
                "dispatch_ref": str(dispatch.get("dispatch_ref") or ""),
                "dispatch_executed": False,
            }
        )

    return candidates, errors


def apply_triage(
    *,
    root: Path,
    candidates: List[Dict[str, Any]],
    target_status: str,
    age_threshold_seconds: int,
    operator: str,
) -> List[Dict[str, Any]]:
    touched: List[Dict[str, Any]] = []

    for item in candidates:
        context_path = Path(item["context_path"])
        context = item["context"]
        instance_id = str(item["instance_id"])

        ts = now_iso()
        stamp = now_stamp()

        evidence_dir = context_path.parent / "evidence"
        triage_evidence_path = evidence_dir / f"state_transition_triage_{stamp}.json"

        triage_event = {
            "timestamp": ts,
            "event": "instance_triaged",
            "instance_id": instance_id,
            "operator": operator,
            "reason": "stale_running_p1_and_dispatch_not_executed",
            "age_seconds": item.get("age_seconds"),
            "age_threshold_seconds": age_threshold_seconds,
            "dispatch_ref": item.get("dispatch_ref"),
            "target_status": target_status,
        }
        dump_json(triage_evidence_path, triage_event)

        phase_results = context["phase_results"]
        last_phase = phase_results[-1]
        # 不新增 phase 记录，直接收敛当前运行相位，避免破坏 control_flow replay 约束。
        last_phase["status"] = "failed"
        last_phase["completed_at"] = ts
        last_phase["output_ref"] = to_rel(triage_evidence_path, root)
        last_phase["transition_on"] = "failure"

        previous_status = str(context.get("status") or "")
        previous_updated = str(context.get("updated_at") or "")

        context["status"] = target_status
        context["updated_at"] = ts

        triage_history = context.get("triage_history")
        if triage_history is None:
            triage_history = []
        triage_history.append(
            {
                "timestamp": ts,
                "operator": operator,
                "action": "converge_backlog_instance",
                "from_status": previous_status,
                "to_status": target_status,
                "reason": "stale_running_p1_and_dispatch_not_executed",
                "dispatch_ref": item.get("dispatch_ref"),
                "age_seconds": item.get("age_seconds"),
                "age_threshold_seconds": age_threshold_seconds,
                "evidence_ref": to_rel(triage_evidence_path, root),
            }
        )
        context["triage_history"] = triage_history

        dump_json(context_path, context)

        touched.append(
            {
                "instance_id": instance_id,
                "context_ref": to_rel(context_path, root),
                "from_status": previous_status,
                "to_status": target_status,
                "from_updated_at": previous_updated,
                "to_updated_at": ts,
                "dispatch_ref": item.get("dispatch_ref"),
                "age_seconds": item.get("age_seconds"),
                "triage_evidence_ref": to_rel(triage_evidence_path, root),
            }
        )

    return touched


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Converge stale M5 backlog instances")
    parser.add_argument(
        "--instance-root",
        action="append",
        dest="instance_roots",
        default=[],
        help="Instance root directory (repeatable)",
    )
    parser.add_argument("--dispatch-glob", default=DEFAULT_DISPATCH_GLOB)
    parser.add_argument("--age-threshold-seconds", type=int, default=3600)
    parser.add_argument("--target-status", choices=["failed", "archived"], default="archived")
    parser.add_argument("--snapshot-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--operator", default="m5-backlog-triage")
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--report", required=True)
    parser.add_argument("--touched-output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    if args.age_threshold_seconds < 1:
        raise TriageError("age_threshold_seconds_must_be_positive")

    raw_roots = args.instance_roots if args.instance_roots else list(DEFAULT_INSTANCE_ROOTS)
    instance_roots = [resolve_path(root, item) for item in raw_roots]

    dispatch_index, dispatch_summary = load_dispatch_index(root, args.dispatch_glob)
    records_before, baseline_before, scan_errors_before = collect_instances(root, instance_roots, args.sample_size)

    report_path = resolve_path(root, args.report)
    touched_path = resolve_path(root, args.touched_output)

    base_report: Dict[str, Any] = {
        "timestamp": now_iso(),
        "status": "ok",
        "snapshot_only": bool(args.snapshot_only),
        "dry_run": bool(args.dry_run),
        "operator": args.operator,
        "target_status": args.target_status,
        "age_threshold_seconds": args.age_threshold_seconds,
        "instance_roots": [to_rel(item, root) for item in instance_roots],
        "dispatch_summary": dispatch_summary,
        "baseline_before": baseline_before,
        "candidate_count": 0,
        "touched_count": 0,
        "baseline_after": None,
        "reason": "",
    }

    touched_payload: Dict[str, Any] = {
        "timestamp": now_iso(),
        "touched_count": 0,
        "items": [],
    }

    if scan_errors_before:
        base_report["status"] = "failed"
        base_report["reason"] = "scan_context_failed"
        dump_json(report_path, base_report)
        dump_json(touched_path, touched_payload)
        print(json.dumps(base_report, ensure_ascii=False))
        return 2

    if args.snapshot_only:
        dump_json(report_path, base_report)
        dump_json(touched_path, touched_payload)
        print(json.dumps(base_report, ensure_ascii=False))
        return 0

    candidates, candidate_errors = choose_candidates(
        records=records_before,
        dispatch_index=dispatch_index,
        age_threshold_seconds=args.age_threshold_seconds,
    )
    base_report["candidate_count"] = len(candidates)

    if candidate_errors:
        base_report["status"] = "failed"
        base_report["reason"] = candidate_errors[0]
        base_report["candidate_errors"] = candidate_errors
        dump_json(report_path, base_report)
        dump_json(touched_path, touched_payload)
        print(json.dumps(base_report, ensure_ascii=False))
        return 2

    touched_items: List[Dict[str, Any]] = []
    if not args.dry_run and candidates:
        touched_items = apply_triage(
            root=root,
            candidates=candidates,
            target_status=args.target_status,
            age_threshold_seconds=args.age_threshold_seconds,
            operator=args.operator,
        )

    records_after, baseline_after, scan_errors_after = collect_instances(root, instance_roots, args.sample_size)
    if scan_errors_after:
        base_report["status"] = "failed"
        base_report["reason"] = "scan_context_after_apply_failed"
        base_report["scan_errors_after"] = scan_errors_after
        dump_json(report_path, base_report)
        dump_json(touched_path, touched_payload)
        print(json.dumps(base_report, ensure_ascii=False))
        return 2

    del records_after  # 当前只用于触发 after 快照采集。

    touched_payload = {
        "timestamp": now_iso(),
        "touched_count": len(touched_items),
        "items": touched_items,
    }

    base_report["touched_count"] = len(touched_items)
    base_report["baseline_after"] = baseline_after
    dump_json(report_path, base_report)
    dump_json(touched_path, touched_payload)
    print(json.dumps(base_report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TriageError as exc:
        print(json.dumps({"status": "failed", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
