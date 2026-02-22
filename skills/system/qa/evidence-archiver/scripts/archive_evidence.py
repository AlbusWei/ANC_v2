#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


def sha256_for(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_ref_manifest(refs: List[str]) -> Dict[str, Any]:
    manifest = {"refs": [], "missing_refs": []}
    for ref in refs:
        path = Path(ref)
        if not path.exists():
            manifest["missing_refs"].append(ref)
            continue
        entry = {
            "ref": ref,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_for(path),
        }
        manifest["refs"].append(entry)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive quality gate evidence")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--profile-id", required=True)
    parser.add_argument("--gate-decision", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--reason", action="append", default=[])
    parser.add_argument("--input-ref", action="append", default=[])
    parser.add_argument("--raw-eval-ref", default="")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    reports_dir = out_dir / "reports"
    raw_dir = out_dir / "raw_eval"
    logs_dir = out_dir / "logs"
    for d in (out_dir, reports_dir, raw_dir, logs_dir):
        d.mkdir(parents=True, exist_ok=True)

    index_ref = out_dir / "index.json"
    verdict_ref = out_dir / "unified_verdict.json"
    archive_report_ref = reports_dir / "archive_report.json"

    try:
        if args.gate_decision not in {"pass", "fail", "hold", "test_invalid"}:
            raise ValueError("invalid_gate_decision")
        if not args.run_id.strip() or not args.profile_id.strip() or not args.actor.strip():
            raise ValueError("missing_required_metadata")

        now = dt.datetime.now(dt.timezone.utc).isoformat()
        reasons = args.reason or ["archived"]
        input_refs = args.input_ref or []
        raw_eval_ref = args.raw_eval_ref.strip()
        if not input_refs and not raw_eval_ref:
            raise ValueError("missing_traceability_inputs")

        manifest_refs = list(input_refs)
        if raw_eval_ref:
            manifest_refs.append(raw_eval_ref)
        manifest = build_ref_manifest(manifest_refs)
        if manifest["missing_refs"]:
            raise ValueError("missing_input_refs:%s" % ",".join(manifest["missing_refs"]))

        index_payload = {
            "run_id": args.run_id,
            "profile_id": args.profile_id,
            "input_refs": input_refs,
            "raw_eval_ref": raw_eval_ref,
            "gate_decision": args.gate_decision,
            "reasons": reasons,
            "actor": args.actor,
            "timestamps": {"archived_at": now},
            "traceability_manifest": manifest,
        }
        index_ref.write_text(json.dumps(index_payload, indent=2), encoding="utf-8")

        verdict_payload = {
            "gate_decision": args.gate_decision,
            "evidence_ref": str(out_dir),
            "reasons": reasons,
            "profile_id": args.profile_id,
            "run_id": args.run_id,
            "raw_eval_ref": raw_eval_ref,
        }
        verdict_ref.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

        report_payload = {
            "status": "pass",
            "evidence_index_ref": str(index_ref),
            "unified_verdict_ref": str(verdict_ref),
            "archive_report_ref": str(archive_report_ref),
            "traceability_manifest_ref": str(index_ref),
        }
        archive_report_ref.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

        output = {
            "evidence_ref": str(out_dir),
            "evidence_index_ref": str(index_ref),
            "archive_report_ref": str(archive_report_ref),
            "gate_decision": args.gate_decision,
            "reasons": reasons,
        }
        print(json.dumps(output, ensure_ascii=True))
        return 0
    except Exception as exc:
        failure = {
            "evidence_ref": str(out_dir),
            "evidence_index_ref": str(index_ref),
            "archive_report_ref": str(archive_report_ref),
            "gate_decision": "fail",
            "reasons": ["exception", str(exc)],
        }
        archive_report_ref.write_text(json.dumps(failure, indent=2), encoding="utf-8")
        print(json.dumps(failure, ensure_ascii=True))
        return 40


if __name__ == "__main__":
    raise SystemExit(main())
