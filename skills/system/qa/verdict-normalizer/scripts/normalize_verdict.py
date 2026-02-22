#!/usr/bin/env python3
import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def load_rules(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(str(path))
    if path.suffix.lower() == ".json":
        return load_json(path)

    text = path.read_text(encoding="utf-8")
    return {
        "precedence": ["fail", "hold", "test_invalid", "pass"],
        "source_type": "markdown",
        "raw_ref": str(path),
        "raw_excerpt": [line.strip() for line in text.splitlines() if "->" in line][:10],
    }


def extract_decision(payload: Dict[str, Any]) -> str:
    for key in ("gate_decision", "evaluation_verdict", "decision", "release_gate_candidate"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    run_payload = payload.get("run")
    if isinstance(run_payload, dict):
        return extract_decision(run_payload)

    subjective_verdict = payload.get("subjective_verdict")
    if subjective_verdict == "accept":
        return "pass"
    if subjective_verdict == "reject":
        return "fail"
    if subjective_verdict == "review":
        return "hold"

    module_runs = payload.get("module_runs")
    if isinstance(module_runs, list) and module_runs:
        module_decisions = [str(item.get("decision", "")).strip() for item in module_runs]
        if any(decision == "fail" for decision in module_decisions):
            return "fail"
        if any(decision == "hold" for decision in module_decisions):
            return "hold"
        if all(decision == "pass" for decision in module_decisions):
            return "pass"

    raise ValueError("missing_decision")


def extract_case_results(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(payload.get("case_results"), list):
        return payload["case_results"]
    run_payload = payload.get("run")
    if isinstance(run_payload, dict) and isinstance(run_payload.get("case_results"), list):
        return run_payload["case_results"]
    return []


def detect_p0_fail(case_results: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    failed_tc_ids: List[str] = []
    for case in case_results:
        if str(case.get("priority", "")).strip() == "P0" and str(case.get("decision", "")).strip() == "fail":
            failed_tc_ids.append(str(case.get("tc_id", "unknown")))
    return bool(failed_tc_ids), failed_tc_ids


def choose_gate(decisions: List[str], has_p0_fail: bool) -> str:
    if has_p0_fail:
        return "fail"
    if "fail" in decisions:
        return "fail"
    if "hold" in decisions:
        return "hold"
    if "test_invalid" in decisions:
        return "test_invalid"
    return "pass"


def code_for(decision: str) -> int:
    if decision == "pass":
        return 0
    if decision == "hold":
        return 30
    if decision == "test_invalid":
        return 20
    return 40


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize evaluation verdicts")
    parser.add_argument("--objective-eval", required=True)
    parser.add_argument("--subjective-eval")
    parser.add_argument("--regression-eval", required=True)
    parser.add_argument("--aggregation-rules", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_ref = out_dir / "aggregation_trace.json"
    verdict_ref = out_dir / "final_gate_verdict.json"

    try:
        rules = load_rules(Path(args.aggregation_rules))
        objective = load_json(Path(args.objective_eval))
        regression = load_json(Path(args.regression_eval))

        decision_map: Dict[str, str] = {
            "objective": extract_decision(objective),
            "regression": extract_decision(regression),
        }
        if args.subjective_eval:
            subjective = load_json(Path(args.subjective_eval))
            decision_map["subjective"] = extract_decision(subjective)

        objective_cases = extract_case_results(objective)
        regression_cases = extract_case_results(regression)
        p0_fail_obj, p0_fail_obj_ids = detect_p0_fail(objective_cases)
        p0_fail_reg, p0_fail_reg_ids = detect_p0_fail(regression_cases)
        has_p0_fail = p0_fail_obj or p0_fail_reg

        decisions = list(decision_map.values())
        gate = choose_gate(decisions, has_p0_fail)
        reasons: List[str] = []
        if has_p0_fail:
            reasons.append("p0_fail")
            reasons.extend(["objective:%s" % tc for tc in p0_fail_obj_ids])
            reasons.extend(["regression:%s" % tc for tc in p0_fail_reg_ids])
        elif gate == "fail":
            reasons.append("evaluation_fail_present")
        elif gate == "hold":
            reasons.append("hold_present")
        elif gate == "test_invalid":
            reasons.append("test_invalid_present")
        else:
            reasons.append("all_evals_pass")

        trace_payload = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "decision_map": decision_map,
            "rules_ref": args.aggregation_rules,
            "rules": rules,
            "p0_fail_detected": has_p0_fail,
            "p0_fail_cases": {
                "objective": p0_fail_obj_ids,
                "regression": p0_fail_reg_ids,
            },
            "final_gate_decision": gate,
        }
        trace_ref.write_text(json.dumps(trace_payload, indent=2), encoding="utf-8")

        verdict_payload = {
            "gate_decision": gate,
            "reasons": reasons,
            "evidence_ref": str(out_dir),
            "final_gate_verdict_ref": str(verdict_ref),
            "aggregation_trace_ref": str(trace_ref),
        }
        verdict_ref.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")
        print(json.dumps(verdict_payload, ensure_ascii=True))
        return code_for(gate)
    except Exception as exc:
        failure = {
            "gate_decision": "fail",
            "reasons": ["exception", str(exc)],
            "evidence_ref": str(out_dir),
            "final_gate_verdict_ref": str(verdict_ref),
            "aggregation_trace_ref": str(trace_ref),
        }
        trace_ref.write_text(json.dumps({"error": str(exc)}, indent=2), encoding="utf-8")
        verdict_ref.write_text(json.dumps(failure, indent=2), encoding="utf-8")
        print(json.dumps(failure, ensure_ascii=True))
        return 40


if __name__ == "__main__":
    raise SystemExit(main())
