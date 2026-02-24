#!/usr/bin/env python3
"""Post-development regression for M6 construction-plane governance assets."""

from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional


Validator = Callable[[subprocess.CompletedProcess[str]], List[str]]


@dataclass
class CaseResult:
    case_id: str
    name: str
    command: List[str]
    return_code: int
    expected_return_code: int
    passed: bool
    reasons: List[str]
    stdout_ref: str
    stderr_ref: str
    payload_ref: str


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def parse_last_json(stdout: str) -> Optional[Dict[str, object]]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("{") and line.endswith("}"):
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
    return None


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def stdout_contains(expected: str) -> Validator:
    def _validator(proc: subprocess.CompletedProcess[str]) -> List[str]:
        if expected in proc.stdout:
            return []
        return [f"stdout_missing:{expected}"]

    return _validator


def stderr_contains(expected: str) -> Validator:
    def _validator(proc: subprocess.CompletedProcess[str]) -> List[str]:
        if expected in proc.stderr:
            return []
        return [f"stderr_missing:{expected}"]

    return _validator


def round_result_validator(
    repo_root: Path,
    round_dir_rel: str,
    expected_status: str,
    expected_failed_phase: Optional[str] = None,
) -> Validator:
    def _validator(proc: subprocess.CompletedProcess[str]) -> List[str]:
        reasons: List[str] = []
        round_result = repo_root / round_dir_rel / "round-result.json"
        if not round_result.exists():
            return [f"missing_round_result:{round_result}"]
        payload = load_json(round_result)
        status = payload.get("status")
        if status != expected_status:
            reasons.append(f"round_status_mismatch:{status}!={expected_status}")
        if expected_failed_phase is not None:
            failed_phase = payload.get("failed_phase")
            if failed_phase != expected_failed_phase:
                reasons.append(f"failed_phase_mismatch:{failed_phase}!={expected_failed_phase}")
        return reasons

    return _validator


def audit_output_validator(
    output_abs: Path,
    expected_decision: str,
    expect_stdout_abs_path: bool,
) -> Validator:
    def _validator(proc: subprocess.CompletedProcess[str]) -> List[str]:
        reasons: List[str] = []
        if expect_stdout_abs_path and proc.stdout.strip() != output_abs.as_posix():
            reasons.append("stdout_not_absolute_output_path")
        if not output_abs.exists():
            reasons.append(f"missing_audit_output:{output_abs}")
            return reasons
        payload = load_json(output_abs)
        decision = payload.get("decision")
        if decision != expected_decision:
            reasons.append(f"audit_decision_mismatch:{decision}!={expected_decision}")
        return reasons

    return _validator


def compile_report_validator(report_path: Path, expected_status: str) -> Validator:
    def _validator(proc: subprocess.CompletedProcess[str]) -> List[str]:
        if not report_path.exists():
            return [f"missing_compile_report:{report_path}"]
        payload = load_json(report_path)
        status = str(payload.get("status", ""))
        if status != expected_status:
            return [f"compile_status_mismatch:{status}!={expected_status}"]
        return []

    return _validator


def evaluation_gate_validator(expected_gate: str) -> Validator:
    def _validator(proc: subprocess.CompletedProcess[str]) -> List[str]:
        payload = parse_last_json(proc.stdout)
        if payload is None:
            return ["missing_json_payload_stdout"]
        gate = str(payload.get("gate_decision", ""))
        if gate != expected_gate:
            return [f"gate_decision_mismatch:{gate}!={expected_gate}"]
        return []

    return _validator


def run_case(
    *,
    repo_root: Path,
    outputs_root: Path,
    case_id: str,
    name: str,
    command: List[str],
    expected_return_code: int,
    validator: Optional[Validator] = None,
    env: Optional[Dict[str, str]] = None,
) -> CaseResult:
    case_dir = outputs_root / "cases" / case_id
    ensure_dir(case_dir)
    completed = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    stdout_path = case_dir / "stdout.txt"
    stderr_path = case_dir / "stderr.txt"
    payload_path = case_dir / "payload.json"
    write_text(stdout_path, completed.stdout)
    write_text(stderr_path, completed.stderr)

    reasons: List[str] = []
    if completed.returncode != expected_return_code:
        reasons.append(
            f"return_code_mismatch:{completed.returncode}!={expected_return_code}"
        )
    if validator is not None:
        reasons.extend(validator(completed))

    parsed_payload = parse_last_json(completed.stdout)
    write_json(
        payload_path,
        {
            "case_id": case_id,
            "name": name,
            "command": command,
            "return_code": completed.returncode,
            "expected_return_code": expected_return_code,
            "passed": len(reasons) == 0,
            "reasons": reasons,
            "stdout_json": parsed_payload,
        },
    )

    return CaseResult(
        case_id=case_id,
        name=name,
        command=command,
        return_code=completed.returncode,
        expected_return_code=expected_return_code,
        passed=len(reasons) == 0,
        reasons=reasons,
        stdout_ref=rel(stdout_path, repo_root),
        stderr_ref=rel(stderr_path, repo_root),
        payload_ref=rel(payload_path, repo_root),
    )


def write_llm_fixture(test_doc_path: Path) -> None:
    content = """# m6-llm-regression - Test Cases

## Objective Alignment

验证 M6 运行结果可进入 LLM-as-Judge 评测通道，并在无效模型时 Fail-Closed。

## Test Cases

### TC-001: M6 结果 LLM 评测契约

- Type: Objective
- Priority: P0
- Input: objective/spec/actual_output_ref
- Expected: round result reports status=passed and includes full p1-p5 completion trace
- Evaluation Method: LLM-Judge
- Judge Payload:
  - objective: verify the M6 round result represents a successfully closed governance round
  - expected_conditions: [phase closure is traceable, fail closed conditions are explicit, evidence references are present]
  - reference_response: round result is passed, p1 to p5 are completed, and output_ref is present
  - grader_selection: [relevance]

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa]
- Grader Selection: [relevance]
- Timeout Seconds: 600
- Retry Policy: max 1
"""
    write_text(test_doc_path, content)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    evidence_root = (
        repo_root
        / "runtime_data/execution/evidence/construction-plane/runtime-validation-round-6"
    )
    fixtures_dir = evidence_root / "fixtures"
    outputs_dir = evidence_root / "outputs"
    ensure_dir(fixtures_dir)
    ensure_dir(outputs_dir)
    shutil.rmtree(outputs_dir / "cases", ignore_errors=True)
    ensure_dir(outputs_dir / "cases")

    round_tmp_rel = "tmp/m6-round-regression-v2"
    round_tmp_dir = repo_root / round_tmp_rel
    shutil.rmtree(round_tmp_dir, ignore_errors=True)

    results: List[CaseResult] = []

    results.append(
        run_case(
            repo_root=repo_root,
            outputs_root=outputs_dir,
            case_id="TC-001",
            name="registry verify pass",
            command=["python3", "shared/registry/registry_contract_tool.py", "verify"],
            expected_return_code=0,
            validator=stdout_contains("Verify passed"),
        )
    )

    scenario_inputs = {
        "A": "runtime_data/execution/evidence/construction-plane/scenario-A-input.json",
        "B": "runtime_data/execution/evidence/construction-plane/scenario-B-input.json",
        "C": "runtime_data/execution/evidence/construction-plane/scenario-C-input.json",
    }
    for scenario, tc_id, expected_rc, expected_phase in [
        ("A", "TC-002", 0, None),
        ("B", "TC-003", 1, "p5"),
        ("C", "TC-004", 1, "p4"),
    ]:
        round_rel = f"{round_tmp_rel}/{scenario}"
        results.append(
            run_case(
                repo_root=repo_root,
                outputs_root=outputs_dir,
                case_id=tc_id,
                name=f"run_round scenario {scenario}",
                command=[
                    "python3",
                    "processes/meta/construction-plane-governance/scripts/run_round.py",
                    "--input",
                    scenario_inputs[scenario],
                    "--round-dir",
                    round_rel,
                    "--scenario",
                    scenario,
                ],
                expected_return_code=expected_rc,
                validator=round_result_validator(
                    repo_root=repo_root,
                    round_dir_rel=round_rel,
                    expected_status="passed" if scenario == "A" else "failed",
                    expected_failed_phase=expected_phase,
                ),
            )
        )

    for scenario, tc_id, expected_rc, expected_err in [
        ("A", "TC-005", 0, None),
        ("B", "TC-006", 1, "checkpoint_count must equal commit_count"),
        ("C", "TC-007", 1, "round_close must be the last event"),
    ]:
        validators: List[Validator] = []
        if expected_err is None:
            validators.append(stdout_contains("verify-m6 passed"))
        else:
            validators.append(stderr_contains(expected_err))

        def chain(vs: List[Validator]) -> Validator:
            def _validator(proc: subprocess.CompletedProcess[str]) -> List[str]:
                out: List[str] = []
                for fn in vs:
                    out.extend(fn(proc))
                return out

            return _validator

        results.append(
            run_case(
                repo_root=repo_root,
                outputs_root=outputs_dir,
                case_id=tc_id,
                name=f"verify-m6 scenario {scenario}",
                command=[
                    "python3",
                    "shared/registry/registry_contract_tool.py",
                    "verify-m6",
                    "--round-dir",
                    f"{round_tmp_rel}/{scenario}",
                ],
                expected_return_code=expected_rc,
                validator=chain(validators),
            )
        )

    audit_input_pass = fixtures_dir / "audit_pass_input.json"
    audit_input_fail = fixtures_dir / "audit_missing_registry_input.json"
    write_json(
        audit_input_pass,
        {
            "round_id": "R-20260221-M6-m6-construction-round-sync-11",
            "scope_baseline_ref": f"{round_tmp_rel}/A/scope_baseline.md",
            "linkage_targets": ["design", "inventory", "registry", "construction_plane"],
            "changed_assets": [
                "docs/design/modules/M6-construction-plane.md",
                "docs/design/processes/construction-plane-governance-process.md",
                "shared/registry/process_registry.json",
            ],
            "openspec_ref": "m6-construction-round-sync",
        },
    )
    write_json(
        audit_input_fail,
        {
            "round_id": "R-20260221-M6-m6-construction-round-sync-11",
            "scope_baseline_ref": f"{round_tmp_rel}/A/scope_baseline.md",
            "linkage_targets": ["design", "inventory", "construction_plane"],
            "changed_assets": [
                "docs/design/modules/M6-construction-plane.md",
                "docs/design/processes/construction-plane-governance-process.md",
                "shared/registry/process_registry.json",
            ],
            "openspec_ref": "m6-construction-round-sync",
        },
    )

    audit_tmp = Path("/tmp/m6-governance-round6")
    audit_tmp.mkdir(parents=True, exist_ok=True)
    audit_pass_out = audit_tmp / "audit-pass-output.json"
    audit_fail_out = audit_tmp / "audit-missing-registry-output.json"

    results.append(
        run_case(
            repo_root=repo_root,
            outputs_root=outputs_dir,
            case_id="TC-008",
            name="construction-audit absolute output path pass",
            command=[
                "python3",
                "skills/system/construction-audit/scripts/construction_audit.py",
                "--input",
                rel(audit_input_pass, repo_root),
                "--output",
                audit_pass_out.as_posix(),
                "--report",
                f"{round_tmp_rel}/A/audit-pass-report.md",
            ],
            expected_return_code=0,
            validator=audit_output_validator(
                output_abs=audit_pass_out,
                expected_decision="pass",
                expect_stdout_abs_path=True,
            ),
        )
    )

    results.append(
        run_case(
            repo_root=repo_root,
            outputs_root=outputs_dir,
            case_id="TC-009",
            name="construction-audit missing registry fail closed",
            command=[
                "python3",
                "skills/system/construction-audit/scripts/construction_audit.py",
                "--input",
                rel(audit_input_fail, repo_root),
                "--output",
                audit_fail_out.as_posix(),
                "--report",
                f"{round_tmp_rel}/A/audit-fail-report.md",
            ],
            expected_return_code=3,
            validator=audit_output_validator(
                output_abs=audit_fail_out,
                expected_decision="fail",
                expect_stdout_abs_path=True,
            ),
        )
    )

    decision_snapshot = repo_root / round_tmp_rel / "A" / "decision_resolved.md"
    round_log_copy = repo_root / round_tmp_rel / "A" / "round-evidence-copy.jsonl"
    write_text(
        decision_snapshot,
        "# Decision Snapshot\nconflict_state: resolved\nowner: architect\n",
    )
    shutil.copyfile(
        repo_root / round_tmp_rel / "A" / "round-evidence.jsonl",
        round_log_copy,
    )

    results.append(
        run_case(
            repo_root=repo_root,
            outputs_root=outputs_dir,
            case_id="TC-010",
            name="openspec-sync count mismatch fail closed",
            command=[
                "bash",
                "skills/system/openspec-sync/scripts/openspec_sync.sh",
                "--round-id",
                "R-20260221-M6-m6-construction-round-sync-11",
                "--round-goal",
                "M6 runtime dry-run scenario A",
                "--openspec-ref",
                "m6-construction-round-sync",
                "--decision-snapshot-ref",
                f"{round_tmp_rel}/A/decision_resolved.md",
                "--sync-actor",
                "architect",
                "--trigger-mode",
                "change_triggered",
                "--risk-level",
                "medium",
                "--checkpoint-count",
                "2",
                "--commit-count",
                "3",
                "--round-evidence-log-ref",
                f"{round_tmp_rel}/A/round-evidence-copy.jsonl",
                "--output-ref",
                f"{round_tmp_rel}/A/openspec-sync-count-mismatch.json",
                "--anc-design-ref",
                "docs/design/modules/M6-construction-plane.md",
            ],
            expected_return_code=15,
            validator=stderr_contains("checkpoint_count must equal commit_count"),
        )
    )

    llm_test_doc = fixtures_dir / "TEST_m6_llm_judge.md"
    write_llm_fixture(llm_test_doc)

    llm_compile_dir = outputs_dir / "test-compiler-llm"
    llm_compile_rel = rel(llm_compile_dir, repo_root)
    results.append(
        run_case(
            repo_root=repo_root,
            outputs_root=outputs_dir,
            case_id="TC-011",
            name="test-compiler m6 llm fixture",
            command=[
                "python3",
                "skills/system/qa/test-compiler/scripts/compile_test_doc.py",
                "--test-doc",
                rel(llm_test_doc, repo_root),
                "--objective-ref",
                "obj-m6-construction-plane-governance",
                "--spec-ref",
                "docs/design/modules/M6-construction-plane.md",
                "--profile-set",
                "quality-gate.baseline@1.0.0",
                "--output-dir",
                llm_compile_rel,
            ],
            expected_return_code=0,
            validator=compile_report_validator(
                llm_compile_dir / "compile_report.json",
                expected_status="pass",
            ),
        )
    )

    preparation_bundle = outputs_dir / "preparation_bundle_m6_llm.index.json"
    write_json(
        preparation_bundle,
        {
            "objective_ref": "obj-m6-construction-plane-governance",
            "spec_ref": "docs/design/modules/M6-construction-plane.md",
            "test_doc_ref": rel(llm_test_doc, repo_root),
            "test_datapoints_ref": rel(llm_compile_dir / "test_datapoints.json", repo_root),
            "tc_profile_map_ref": rel(llm_compile_dir / "tc_profile_map.json", repo_root),
            "compile_report_ref": rel(llm_compile_dir / "compile_report.json", repo_root),
            "producer_process_id": "quality-gate-preparation",
            "timestamps": {"generated_at": now_utc()},
        },
    )

    eval_llm_live_dir = outputs_dir / "evaluation-runner-llm-live"
    eval_llm_invalid_model_dir = outputs_dir / "evaluation-runner-llm-invalid-model"

    results.append(
        run_case(
            repo_root=repo_root,
            outputs_root=outputs_dir,
            case_id="TC-012",
            name="evaluation-runner llm available pass",
            command=[
                "skills/system/qa/evaluation-runner/scripts/quality_eval_runner",
                "run",
                "--preparation-bundle",
                rel(preparation_bundle, repo_root),
                "--mode",
                "objective",
                "--actual-output",
                f"{round_tmp_rel}/A/round-result.json",
                "--judge-model",
                "gpt-5.3-codex",
                "--module",
                "M6",
                "--output-dir",
                rel(eval_llm_live_dir, repo_root),
            ],
            expected_return_code=0,
            validator=evaluation_gate_validator("pass"),
        )
    )

    results.append(
        run_case(
            repo_root=repo_root,
            outputs_root=outputs_dir,
            case_id="TC-013",
            name="evaluation-runner llm invalid model fail closed",
            command=[
                "skills/system/qa/evaluation-runner/scripts/quality_eval_runner",
                "run",
                "--preparation-bundle",
                rel(preparation_bundle, repo_root),
                "--mode",
                "objective",
                "--actual-output",
                f"{round_tmp_rel}/A/round-result.json",
                "--judge-model",
                "invalid-model-for-fail-closed",
                "--module",
                "M6",
                "--output-dir",
                rel(eval_llm_invalid_model_dir, repo_root),
            ],
            expected_return_code=20,
            validator=evaluation_gate_validator("test_invalid"),
        )
    )

    failed = [case for case in results if not case.passed]
    gate_decision = "pass" if not failed else "fail"
    reasons = ["all_cases_passed"] if not failed else [f"{case.case_id}:{';'.join(case.reasons)}" for case in failed]

    report = {
        "gate_decision": gate_decision,
        "evidence_ref": rel(outputs_dir, repo_root),
        "reasons": reasons,
        "case_count": len(results),
        "passed_count": len(results) - len(failed),
        "failed_count": len(failed),
        "generated_at": now_utc(),
        "case_results": [asdict(case) for case in results],
    }
    report_path = outputs_dir / "regression_report.json"
    write_json(report_path, report)

    summary_lines = [
        "# M6 Runtime Validation Round 6 - Regression Summary",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- gate_decision: {gate_decision}",
        f"- case_count: {report['case_count']}",
        f"- passed_count: {report['passed_count']}",
        f"- failed_count: {report['failed_count']}",
        "",
        "## Case Results",
    ]
    for case in results:
        status = "PASS" if case.passed else "FAIL"
        summary_lines.append(
            f"- {case.case_id} [{status}] rc={case.return_code}/{case.expected_return_code} {case.name}"
        )
    summary_lines.extend(["", "## Reasons"])
    for reason in reasons:
        summary_lines.append(f"- {reason}")
    summary_path = outputs_dir / "regression_summary.md"
    write_text(summary_path, "\n".join(summary_lines) + "\n")

    print(rel(report_path, repo_root))
    return 0 if gate_decision == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
