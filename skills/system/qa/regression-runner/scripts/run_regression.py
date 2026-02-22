#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def parse_modules(scope: str) -> List[str]:
    return [item.strip() for item in scope.split(",") if item.strip()]


def normalize_decision(return_code: int, payload: Dict[str, Any]) -> str:
    decision = str(payload.get("gate_decision") or payload.get("evaluation_verdict") or "").strip()
    if decision in {"pass", "fail", "hold", "test_invalid"}:
        return "fail" if decision == "test_invalid" else decision
    if return_code == 0:
        return "pass"
    if return_code == 30:
        return "hold"
    return "fail"


def resolve_module_outputs(modules: List[str], output_refs: List[str]) -> Dict[str, List[str]]:
    if not output_refs:
        raise ValueError("missing_actual_output")

    if len(output_refs) == 1:
        return {module: [output_refs[0]] for module in modules}
    if len(output_refs) == len(modules):
        return {module: [output_refs[index]] for index, module in enumerate(modules)}
    if len(output_refs) == len(modules) * 2:
        return {
            module: [output_refs[index * 2], output_refs[(index * 2) + 1]]
            for index, module in enumerate(modules)
        }
    raise ValueError("ambiguous_actual_output_mapping")


def parse_last_json(stdout: str) -> Dict[str, Any]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise ValueError("runner_no_output")
    for line in reversed(lines):
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise ValueError("runner_output_no_json")


def candidate_for(decisions: List[str]) -> str:
    if any(decision == "fail" for decision in decisions):
        return "fail"
    if any(decision == "hold" for decision in decisions):
        return "hold"
    return "pass"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run cross-module regression orchestration")
    parser.add_argument("--regression-scope", required=True)
    parser.add_argument("--profile-set", required=True)
    parser.add_argument("--preparation-bundle", required=True)
    parser.add_argument("--actual-output", action="append", default=[])
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--evaluation-runner",
        default="skills/system/qa/evaluation-runner/scripts/quality_eval_runner",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    eval_json_ref = out_dir / "regression_eval.json"
    report_ref = out_dir / "regression_report.json"

    modules = parse_modules(args.regression_scope)
    if not modules:
        payload = {
            "regression_eval_ref": str(eval_json_ref),
            "regression_report_ref": str(report_ref),
            "release_gate_candidate": "fail",
            "gate_decision": "fail",
            "evidence_ref": str(out_dir),
            "reasons": ["empty_regression_scope"],
        }
        report_ref.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=True))
        return 40

    try:
        module_outputs = resolve_module_outputs(modules, args.actual_output)
    except ValueError as exc:
        payload = {
            "regression_eval_ref": str(eval_json_ref),
            "regression_report_ref": str(report_ref),
            "release_gate_candidate": "fail",
            "gate_decision": "fail",
            "evidence_ref": str(out_dir),
            "reasons": [str(exc)],
        }
        report_ref.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=True))
        return 40

    module_runs: List[Dict[str, Any]] = []
    decisions: List[str] = []

    try:
        for module in modules:
            module_dir = out_dir / module
            module_dir.mkdir(parents=True, exist_ok=True)

            cmd = [
                args.evaluation_runner,
                "run",
                "--preparation-bundle",
                args.preparation_bundle,
                "--mode",
                "regression",
                "--module",
                module,
                "--output-dir",
                str(module_dir),
            ]
            for output_ref in module_outputs[module]:
                cmd.extend(["--actual-output", output_ref])

            completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
            payload = parse_last_json(completed.stdout)
            decision = normalize_decision(completed.returncode, payload)
            decisions.append(decision)

            module_runs.append(
                {
                    "module": module,
                    "actual_output_refs": module_outputs[module],
                    "return_code": completed.returncode,
                    "decision": decision,
                    "payload": payload,
                    "stderr": completed.stderr.strip(),
                }
            )

        release_candidate = candidate_for(decisions)
        timestamp = dt.datetime.now(dt.timezone.utc).isoformat()

        eval_payload = {
            "timestamp": timestamp,
            "profile_set": args.profile_set,
            "preparation_bundle_ref": args.preparation_bundle,
            "module_runs": module_runs,
            "release_gate_candidate": release_candidate,
        }
        eval_json_ref.write_text(json.dumps(eval_payload, indent=2), encoding="utf-8")

        report_payload = {
            "modules": modules,
            "profile_set": args.profile_set,
            "summary": {
                "pass": sum(1 for decision in decisions if decision == "pass"),
                "hold": sum(1 for decision in decisions if decision == "hold"),
                "fail": sum(1 for decision in decisions if decision == "fail"),
            },
            "release_gate_candidate": release_candidate,
            "module_eval_refs": [str(out_dir / module / "raw_eval.json") for module in modules],
            "generated_at": timestamp,
        }
        report_ref.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

        output = {
            "regression_eval_ref": str(eval_json_ref),
            "regression_report_ref": str(report_ref),
            "release_gate_candidate": release_candidate,
            "gate_decision": release_candidate,
            "evidence_ref": str(out_dir),
            "reasons": ["regression_orchestration_completed"],
        }
        print(json.dumps(output, ensure_ascii=True))
        return 0 if release_candidate == "pass" else (30 if release_candidate == "hold" else 40)
    except Exception as exc:
        output = {
            "regression_eval_ref": str(eval_json_ref),
            "regression_report_ref": str(report_ref),
            "release_gate_candidate": "fail",
            "gate_decision": "fail",
            "evidence_ref": str(out_dir),
            "reasons": ["exception", str(exc)],
        }
        report_ref.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(json.dumps(output, ensure_ascii=True))
        return 40


if __name__ == "__main__":
    raise SystemExit(main())
