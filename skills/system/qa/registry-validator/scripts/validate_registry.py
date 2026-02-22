#!/usr/bin/env python3
import argparse
import json
import subprocess
import datetime as dt
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ANC registry contracts")
    parser.add_argument("--registry-tool", required=True)
    parser.add_argument("--verify-scope", default="skill_registry")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_ref = out_dir / "registry_validation_report.json"

    try:
        cmd = ["python3", args.registry_tool, "verify"]
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)

        decision = "pass" if completed.returncode == 0 else "fail"
        reasons = ["verify_passed"] if decision == "pass" else ["verify_failed"]
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()

        parsed_stdout = None
        if stdout.startswith("{") and stdout.endswith("}"):
            try:
                parsed_stdout = json.loads(stdout)
            except json.JSONDecodeError:
                parsed_stdout = None

        payload = {
            "verify_scope": args.verify_scope,
            "validation_report_ref": str(report_ref),
            "gate_decision": decision,
            "evidence_ref": str(out_dir),
            "reasons": reasons,
            "return_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "parsed_stdout": parsed_stdout,
            "validated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        report_ref.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=True))
        return 0 if decision == "pass" else 40
    except Exception as exc:
        payload = {
            "verify_scope": args.verify_scope,
            "validation_report_ref": str(report_ref),
            "gate_decision": "fail",
            "evidence_ref": str(out_dir),
            "reasons": ["exception", str(exc)],
        }
        report_ref.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=True))
        return 40


if __name__ == "__main__":
    raise SystemExit(main())
