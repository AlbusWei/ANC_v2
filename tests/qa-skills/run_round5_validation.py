#!/usr/bin/env python3
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CaseResult:
    case_id: str
    name: str
    command: List[str]
    return_code: int
    expected_return_code: int
    gate_decision: str
    expected_gate_decision: str
    passed: bool
    reasons: List[str]
    stdout_ref: str
    stderr_ref: str
    payload_ref: str


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def parse_last_json(stdout: str) -> Dict[str, Any]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise ValueError("missing_json_stdout")


def run_case(
    *,
    repo_root: Path,
    case_id: str,
    name: str,
    command: List[str],
    expected_return_code: int,
    expected_gate_decision: str,
    out_dir: Path,
) -> CaseResult:
    ensure_dir(out_dir)
    completed = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)

    stdout_ref = out_dir / "stdout.txt"
    stderr_ref = out_dir / "stderr.txt"
    payload_ref = out_dir / "payload.json"
    stdout_ref.write_text(completed.stdout, encoding="utf-8")
    stderr_ref.write_text(completed.stderr, encoding="utf-8")

    reasons: List[str] = []
    gate_decision = "<parse_error>"
    passed = True

    try:
        payload = parse_last_json(completed.stdout)
    except Exception as exc:
        payload = {"parse_error": str(exc)}
        passed = False
        reasons.append("payload_parse_error:%s" % exc)

    if "gate_decision" in payload and isinstance(payload["gate_decision"], str):
        gate_decision = payload["gate_decision"].strip()
    elif "release_gate_candidate" in payload and isinstance(payload["release_gate_candidate"], str):
        gate_decision = payload["release_gate_candidate"].strip()
    elif "evaluation_verdict" in payload and isinstance(payload["evaluation_verdict"], str):
        gate_decision = payload["evaluation_verdict"].strip()

    if completed.returncode != expected_return_code:
        passed = False
        reasons.append("return_code_mismatch:%s!=%s" % (completed.returncode, expected_return_code))

    if gate_decision != expected_gate_decision:
        passed = False
        reasons.append("gate_decision_mismatch:%s!=%s" % (gate_decision, expected_gate_decision))

    write_json(
        payload_ref,
        {
            "case_id": case_id,
            "name": name,
            "command": command,
            "return_code": completed.returncode,
            "expected_return_code": expected_return_code,
            "gate_decision": gate_decision,
            "expected_gate_decision": expected_gate_decision,
            "payload": payload,
            "passed": passed,
            "reasons": reasons,
        },
    )

    return CaseResult(
        case_id=case_id,
        name=name,
        command=command,
        return_code=completed.returncode,
        expected_return_code=expected_return_code,
        gate_decision=gate_decision,
        expected_gate_decision=expected_gate_decision,
        passed=passed,
        reasons=reasons,
        stdout_ref=str(stdout_ref.relative_to(repo_root)),
        stderr_ref=str(stderr_ref.relative_to(repo_root)),
        payload_ref=str(payload_ref.relative_to(repo_root)),
    )


def make_preparation_bundle(
    *,
    root: Path,
    bundle_ref: Path,
    compile_output_dir: Path,
    test_doc_ref: str,
    objective_ref: str,
    spec_ref: str,
) -> None:
    payload = {
        "objective_ref": objective_ref,
        "spec_ref": spec_ref,
        "test_doc_ref": test_doc_ref,
        "test_datapoints_ref": str((compile_output_dir / "test_datapoints.json").relative_to(root)),
        "tc_profile_map_ref": str((compile_output_dir / "tc_profile_map.json").relative_to(root)),
        "compile_report_ref": str((compile_output_dir / "compile_report.json").relative_to(root)),
        "producer_process_id": "quality-gate-preparation",
        "timestamps": {"generated_at": now_utc()},
    }
    write_json(bundle_ref, payload)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    evidence_root = repo_root / "runtime_data/execution/evidence/quality-gate/runtime-validation-round-5"
    fixtures_dir = evidence_root / "fixtures"
    outputs_dir = evidence_root / "outputs"
    ensure_dir(fixtures_dir)
    ensure_dir(outputs_dir)

    objective_ref = "obj-m1-unified-quality-gate"
    spec_ref = "docs/design/modules/M1-openjudge-adapter-spec.md"
    profile = "quality-gate.baseline@1.0.0"

    rule_test_doc = "tests/fixtures/quality-gate/TEST_rule.md"
    actual_output_pass = "tests/fixtures/quality-gate/actual_output_pass.txt"
    actual_output_baseline = "tests/fixtures/quality-gate/actual_output_baseline.txt"
    actual_output_candidate = "tests/fixtures/quality-gate/actual_output_candidate.txt"

    results: List[CaseResult] = []

    compile_pass_dir = outputs_dir / "test-compiler-pass"
    compile_invalid_dir = outputs_dir / "test-compiler-empty-profile"

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-001",
            name="test-compiler pass",
            command=[
                "python3",
                "skills/system/qa/test-compiler/scripts/compile_test_doc.py",
                "--test-doc",
                rule_test_doc,
                "--objective-ref",
                objective_ref,
                "--spec-ref",
                spec_ref,
                "--profile-set",
                profile,
                "--output-dir",
                str(compile_pass_dir.relative_to(repo_root)),
            ],
            expected_return_code=0,
            expected_gate_decision="pass",
            out_dir=compile_pass_dir,
        )
    )

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-002",
            name="test-compiler empty profile fail-closed",
            command=[
                "python3",
                "skills/system/qa/test-compiler/scripts/compile_test_doc.py",
                "--test-doc",
                rule_test_doc,
                "--objective-ref",
                objective_ref,
                "--spec-ref",
                spec_ref,
                "--profile-set",
                "",
                "--output-dir",
                str(compile_invalid_dir.relative_to(repo_root)),
            ],
            expected_return_code=20,
            expected_gate_decision="test_invalid",
            out_dir=compile_invalid_dir,
        )
    )

    bundle_ref = outputs_dir / "preparation_bundle.index.json"
    make_preparation_bundle(
        root=repo_root,
        bundle_ref=bundle_ref,
        compile_output_dir=compile_pass_dir,
        test_doc_ref=rule_test_doc,
        objective_ref=objective_ref,
        spec_ref=spec_ref,
    )

    eval_objective_dir = outputs_dir / "evaluation-runner-objective"
    eval_missing_output_dir = outputs_dir / "evaluation-runner-missing-output"
    eval_regression_dir = outputs_dir / "evaluation-runner-regression"

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-003",
            name="evaluation-runner objective pass",
            command=[
                "skills/system/qa/evaluation-runner/scripts/quality_eval_runner",
                "run",
                "--preparation-bundle",
                str(bundle_ref.relative_to(repo_root)),
                "--mode",
                "objective",
                "--actual-output",
                actual_output_pass,
                "--module",
                "M3",
                "--output-dir",
                str(eval_objective_dir.relative_to(repo_root)),
            ],
            expected_return_code=0,
            expected_gate_decision="pass",
            out_dir=eval_objective_dir,
        )
    )

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-004",
            name="evaluation-runner missing actual output",
            command=[
                "skills/system/qa/evaluation-runner/scripts/quality_eval_runner",
                "run",
                "--preparation-bundle",
                str(bundle_ref.relative_to(repo_root)),
                "--mode",
                "objective",
                "--module",
                "M3",
                "--output-dir",
                str(eval_missing_output_dir.relative_to(repo_root)),
            ],
            expected_return_code=20,
            expected_gate_decision="test_invalid",
            out_dir=eval_missing_output_dir,
        )
    )

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-005A",
            name="evaluation-runner regression pass for normalizer input",
            command=[
                "skills/system/qa/evaluation-runner/scripts/quality_eval_runner",
                "run",
                "--preparation-bundle",
                str(bundle_ref.relative_to(repo_root)),
                "--mode",
                "regression",
                "--actual-output",
                actual_output_pass,
                "--module",
                "M3",
                "--output-dir",
                str(eval_regression_dir.relative_to(repo_root)),
            ],
            expected_return_code=0,
            expected_gate_decision="pass",
            out_dir=eval_regression_dir,
        )
    )

    objective_eval_ref = eval_objective_dir / "raw_eval.json"
    regression_eval_ref = eval_regression_dir / "raw_eval.json"
    aggregation_rules_ref = repo_root / "tests/fixtures/quality-gate/aggregation_rules.json"

    verdict_pass_dir = outputs_dir / "verdict-normalizer-pass"
    verdict_test_invalid_dir = outputs_dir / "verdict-normalizer-test-invalid"

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-005",
            name="verdict-normalizer pass aggregation",
            command=[
                "python3",
                "skills/system/qa/verdict-normalizer/scripts/normalize_verdict.py",
                "--objective-eval",
                str(objective_eval_ref.relative_to(repo_root)),
                "--regression-eval",
                str(regression_eval_ref.relative_to(repo_root)),
                "--aggregation-rules",
                str(aggregation_rules_ref.relative_to(repo_root)),
                "--output-dir",
                str(verdict_pass_dir.relative_to(repo_root)),
            ],
            expected_return_code=0,
            expected_gate_decision="pass",
            out_dir=verdict_pass_dir,
        )
    )

    objective_test_invalid_ref = fixtures_dir / "objective_test_invalid.json"
    regression_pass_ref = fixtures_dir / "regression_pass.json"
    write_json(
        objective_test_invalid_ref,
        {
            "gate_decision": "test_invalid",
            "case_results": [
                {
                    "tc_id": "TC-X",
                    "priority": "P0",
                    "decision": "test_invalid",
                }
            ],
        },
    )
    write_json(
        regression_pass_ref,
        {
            "gate_decision": "pass",
            "module_runs": [
                {"module": "M3", "decision": "pass"},
            ],
        },
    )

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-006",
            name="verdict-normalizer test_invalid propagation",
            command=[
                "python3",
                "skills/system/qa/verdict-normalizer/scripts/normalize_verdict.py",
                "--objective-eval",
                str(objective_test_invalid_ref.relative_to(repo_root)),
                "--regression-eval",
                str(regression_pass_ref.relative_to(repo_root)),
                "--aggregation-rules",
                str(aggregation_rules_ref.relative_to(repo_root)),
                "--output-dir",
                str(verdict_test_invalid_dir.relative_to(repo_root)),
            ],
            expected_return_code=20,
            expected_gate_decision="test_invalid",
            out_dir=verdict_test_invalid_dir,
        )
    )

    hold_case_ref = fixtures_dir / "hold_case_no_progress.json"
    runtime_log_ref = fixtures_dir / "runtime_no_progress.log"
    runtime_prev_ref = fixtures_dir / "runtime_no_progress_prev.log"
    exec_state_ref = fixtures_dir / "execution_state_no_progress.json"
    exec_prev_ref = fixtures_dir / "execution_state_no_progress_prev.json"
    triage_policy_ref = fixtures_dir / "triage_policy_restricted.json"

    write_json(
        hold_case_ref,
        {
            "last_output_heartbeat_at": "2025-01-01T00:00:00+00:00",
        },
    )
    runtime_log_ref.write_text("step-1 done\n", encoding="utf-8")
    runtime_prev_ref.write_text("step-1 done\n", encoding="utf-8")
    write_json(exec_state_ref, {"state": "running", "phase_progress": "eval_running", "phase_index": 2})
    write_json(exec_prev_ref, {"state": "running", "phase_progress": "eval_running", "phase_index": 2})
    write_json(
        triage_policy_ref,
        {
            "allowed_actions": ["fail"],
            "heartbeat_max_age_seconds": 1,
            "on_no_progress": "continue",
        },
    )

    hold_triage_dir = outputs_dir / "hold-triage-policy-restricted"
    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-007",
            name="hold-triage restricted policy fail-closed",
            command=[
                "python3",
                "skills/system/qa/hold-triage/scripts/hold_triage.py",
                "--hold-case",
                str(hold_case_ref.relative_to(repo_root)),
                "--runtime-log",
                str(runtime_log_ref.relative_to(repo_root)),
                "--execution-state",
                str(exec_state_ref.relative_to(repo_root)),
                "--triage-policy",
                str(triage_policy_ref.relative_to(repo_root)),
                "--previous-runtime-log",
                str(runtime_prev_ref.relative_to(repo_root)),
                "--previous-execution-state",
                str(exec_prev_ref.relative_to(repo_root)),
                "--output-dir",
                str(hold_triage_dir.relative_to(repo_root)),
            ],
            expected_return_code=40,
            expected_gate_decision="fail",
            out_dir=hold_triage_dir,
        )
    )

    regression_runner_pass_dir = outputs_dir / "regression-runner-pass"
    regression_runner_ambiguous_dir = outputs_dir / "regression-runner-ambiguous"

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-008",
            name="regression-runner pass",
            command=[
                "python3",
                "skills/system/qa/regression-runner/scripts/run_regression.py",
                "--regression-scope",
                "M3,M4",
                "--profile-set",
                profile,
                "--preparation-bundle",
                str(bundle_ref.relative_to(repo_root)),
                "--actual-output",
                actual_output_pass,
                "--output-dir",
                str(regression_runner_pass_dir.relative_to(repo_root)),
            ],
            expected_return_code=0,
            expected_gate_decision="pass",
            out_dir=regression_runner_pass_dir,
        )
    )

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-009",
            name="regression-runner ambiguous output mapping",
            command=[
                "python3",
                "skills/system/qa/regression-runner/scripts/run_regression.py",
                "--regression-scope",
                "M3,M4,M5",
                "--profile-set",
                profile,
                "--preparation-bundle",
                str(bundle_ref.relative_to(repo_root)),
                "--actual-output",
                actual_output_baseline,
                "--actual-output",
                actual_output_candidate,
                "--output-dir",
                str(regression_runner_ambiguous_dir.relative_to(repo_root)),
            ],
            expected_return_code=40,
            expected_gate_decision="fail",
            out_dir=regression_runner_ambiguous_dir,
        )
    )

    registry_validator_pass_dir = outputs_dir / "registry-validator-pass"
    registry_validator_missing_tool_dir = outputs_dir / "registry-validator-missing-tool"

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-010",
            name="registry-validator pass",
            command=[
                "python3",
                "skills/system/qa/registry-validator/scripts/validate_registry.py",
                "--registry-tool",
                "shared/registry/registry_contract_tool.py",
                "--verify-scope",
                "skill_registry",
                "--output-dir",
                str(registry_validator_pass_dir.relative_to(repo_root)),
            ],
            expected_return_code=0,
            expected_gate_decision="pass",
            out_dir=registry_validator_pass_dir,
        )
    )

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-011",
            name="registry-validator missing tool fail-closed",
            command=[
                "python3",
                "skills/system/qa/registry-validator/scripts/validate_registry.py",
                "--registry-tool",
                "shared/registry/not_exists_tool.py",
                "--verify-scope",
                "skill_registry",
                "--output-dir",
                str(registry_validator_missing_tool_dir.relative_to(repo_root)),
            ],
            expected_return_code=40,
            expected_gate_decision="fail",
            out_dir=registry_validator_missing_tool_dir,
        )
    )

    evidence_archiver_pass_dir = outputs_dir / "evidence-archiver-pass"
    evidence_archiver_missing_trace_dir = outputs_dir / "evidence-archiver-missing-trace"

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-012",
            name="evidence-archiver pass",
            command=[
                "python3",
                "skills/system/qa/evidence-archiver/scripts/archive_evidence.py",
                "--run-id",
                "round5-001",
                "--profile-id",
                profile,
                "--gate-decision",
                "pass",
                "--actor",
                "qa",
                "--reason",
                "round5_pass",
                "--input-ref",
                actual_output_pass,
                "--raw-eval-ref",
                str(objective_eval_ref.relative_to(repo_root)),
                "--output-dir",
                str(evidence_archiver_pass_dir.relative_to(repo_root)),
            ],
            expected_return_code=0,
            expected_gate_decision="pass",
            out_dir=evidence_archiver_pass_dir,
        )
    )

    results.append(
        run_case(
            repo_root=repo_root,
            case_id="TC-013",
            name="evidence-archiver missing traceability inputs",
            command=[
                "python3",
                "skills/system/qa/evidence-archiver/scripts/archive_evidence.py",
                "--run-id",
                "round5-002",
                "--profile-id",
                profile,
                "--gate-decision",
                "pass",
                "--actor",
                "qa",
                "--output-dir",
                str(evidence_archiver_missing_trace_dir.relative_to(repo_root)),
            ],
            expected_return_code=40,
            expected_gate_decision="fail",
            out_dir=evidence_archiver_missing_trace_dir,
        )
    )

    total = len(results)
    passed_cases = [item for item in results if item.passed]
    failed_cases = [item for item in results if not item.passed]

    summary = {
        "round": "runtime-validation-round-5",
        "generated_at": now_utc(),
        "scope": [
            "sys.qa.test-compiler",
            "sys.qa.evaluation-runner",
            "sys.qa.verdict-normalizer",
            "sys.qa.hold-triage",
            "sys.qa.regression-runner",
            "sys.qa.registry-validator",
            "sys.qa.evidence-archiver",
        ],
        "total_cases": total,
        "passed_cases": len(passed_cases),
        "failed_cases": len(failed_cases),
        "gate_decision": "pass" if not failed_cases else "fail",
        "cases": [
            {
                "case_id": item.case_id,
                "name": item.name,
                "return_code": item.return_code,
                "expected_return_code": item.expected_return_code,
                "gate_decision": item.gate_decision,
                "expected_gate_decision": item.expected_gate_decision,
                "passed": item.passed,
                "reasons": item.reasons,
                "stdout_ref": item.stdout_ref,
                "stderr_ref": item.stderr_ref,
                "payload_ref": item.payload_ref,
            }
            for item in results
        ],
    }

    summary_ref = outputs_dir / "runtime_summary.json"
    write_json(summary_ref, summary)

    if failed_cases:
        print(json.dumps({
            "gate_decision": "fail",
            "failed_cases": [item.case_id for item in failed_cases],
            "runtime_summary_ref": str(summary_ref.relative_to(repo_root)),
        }, ensure_ascii=True))
        return 1

    print(json.dumps({
        "gate_decision": "pass",
        "total_cases": total,
        "runtime_summary_ref": str(summary_ref.relative_to(repo_root)),
    }, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
