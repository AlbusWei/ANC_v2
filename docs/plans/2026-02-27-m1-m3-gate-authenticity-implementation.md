# M1/M3 Gate Authenticity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a strict admission gate that only accepts real online evidence (not simulated/skeleton outputs), while keeping runtime evidence under `tmp/runtime_data/...` to avoid repository pollution.

**Architecture:** Add a centralized evidence verification step at final gate aggregation (single source of truth), then wire M1 regression and M3 online runners to produce and validate the same minimum evidence chain. Keep schema changes minimal by validating evidence artifacts and traceability references rather than introducing many new protocol fields.

**Tech Stack:** Python 3, existing M1/M3 runners, OpenClaw CLI traces, JSON evidence artifacts, markdown design docs.

---

### Task 1: Add failing regression test for strict evidence verification in M1 gate

**Files:**
- Create: `tests/m1-runtime/test_gate_evidence_verifier.py`
- Modify: `tests/m1-runtime/TEST.md`
- Reference: `processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from processes.meta.quality_gate_evaluation.scripts.quality_gate_evaluation_runner import (
    verify_gate_evidence_chain,
)


def test_gate_fails_without_openclaw_trace(tmp_path: Path):
    payload = {
        "dispatch_trace_ref": "",
        "phase_outputs": ["tmp/runtime_data/evidence/p1.json"],
        "case_report_ref": "tmp/runtime_data/evidence/case_report.json",
    }
    ok, reason = verify_gate_evidence_chain(payload, repo_root=tmp_path)
    assert ok is False
    assert reason == "missing_openclaw_trace"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/m1-runtime/test_gate_evidence_verifier.py -q`
Expected: FAIL with import/function not found (`verify_gate_evidence_chain` not defined).

**Step 3: Write minimal implementation scaffold**

```python
def verify_gate_evidence_chain(payload: dict, repo_root: Path):
    return False, "missing_openclaw_trace"
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/m1-runtime/test_gate_evidence_verifier.py -q`
Expected: PASS (single test).

**Step 5: Commit**

```bash
git add tests/m1-runtime/test_gate_evidence_verifier.py tests/m1-runtime/TEST.md processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py
git commit -m "test: add failing evidence-chain gate check baseline"
```

---

### Task 2: Implement centralized evidence-chain verifier in quality gate evaluation

**Files:**
- Modify: `processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py`
- Modify: `tests/fixtures/quality-gate/aggregation_rules.json`
- Test: `tests/m1-runtime/test_gate_evidence_verifier.py`

**Step 1: Extend failing tests for full minimum evidence set**

```python
def test_gate_fails_when_phase_output_missing(tmp_path: Path):
    payload = {
        "dispatch_trace_ref": "tmp/runtime_data/evidence/dispatch.json",
        "phase_outputs": ["tmp/runtime_data/evidence/missing_p2.json"],
        "case_report_ref": "tmp/runtime_data/evidence/case_report.json",
    }
    ok, reason = verify_gate_evidence_chain(payload, repo_root=tmp_path)
    assert ok is False
    assert reason == "missing_phase_output"


def test_gate_fails_when_case_report_missing_fail_and_rollback_assertions(tmp_path: Path):
    payload = {
        "dispatch_trace_ref": "tmp/runtime_data/evidence/dispatch.json",
        "phase_outputs": ["tmp/runtime_data/evidence/p1.json"],
        "case_report_ref": "tmp/runtime_data/evidence/case_report.json",
    }
    ok, reason = verify_gate_evidence_chain(payload, repo_root=tmp_path)
    assert ok is False
    assert reason == "case_report_not_representative"
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/m1-runtime/test_gate_evidence_verifier.py -q`
Expected: FAIL for new scenarios.

**Step 3: Implement minimal real verifier logic**

```python
def verify_gate_evidence_chain(payload: dict, repo_root: Path):
    dispatch_ref = str(payload.get("dispatch_trace_ref") or "").strip()
    if not dispatch_ref:
        return False, "missing_openclaw_trace"
    dispatch_path = resolve_path(repo_root, dispatch_ref)
    if not dispatch_path.exists():
        return False, "missing_openclaw_trace"

    phase_outputs = payload.get("phase_outputs") or []
    if not isinstance(phase_outputs, list) or not phase_outputs:
        return False, "missing_phase_output"
    for ref in phase_outputs:
        if not resolve_path(repo_root, str(ref)).exists():
            return False, "missing_phase_output"

    case_report_ref = str(payload.get("case_report_ref") or "").strip()
    case_report_path = resolve_path(repo_root, case_report_ref)
    if not case_report_ref or not case_report_path.exists():
        return False, "missing_case_report"

    report = load_json(case_report_path)
    assertions = report.get("assertions") if isinstance(report, dict) else None
    has_fail_path = isinstance(assertions, dict) and bool(assertions.get("failure_path"))
    has_rollback_path = isinstance(assertions, dict) and bool(assertions.get("rollback_path"))
    if not (has_fail_path and has_rollback_path):
        return False, "case_report_not_representative"

    return True, "ok"
```

**Step 4: Enforce verifier before pass decision is emitted**

```python
verified, verify_reason = verify_gate_evidence_chain(request, root)
if not verified:
    gate_decision = "fail"
    runtime_gate_state = "fail"
    phase_trace.append({"phase": "evidence-verification", "status": "failed", "reason": verify_reason})
```

**Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/m1-runtime/test_gate_evidence_verifier.py -q`
Expected: PASS.

**Step 6: Run M1 regression smoke**

Run: `python3 tests/m1-runtime/run_post_dev_regression.py`
Expected: Existing pass/fail-closed/hold suites still execute; no false pass without evidence chain.

**Step 7: Commit**

```bash
git add processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py tests/m1-runtime/test_gate_evidence_verifier.py tests/fixtures/quality-gate/aggregation_rules.json
git commit -m "feat: enforce centralized evidence-chain verification for gate admission"
```

---

### Task 3: Align evidence output policy to tmp runtime path (non-repo-polluting)

**Files:**
- Modify: `tests/m1-runtime/TEST.md`
- Modify: `tests/m3-self-development/TEST.md`
- Modify: `docs/design/modules/M1-test-system.md`
- Modify: `docs/architecture/construction_plane.md`
- Modify: `tests/m1-runtime/run_post_dev_regression.py` (defaults only)
- Modify: `tests/m3-self-development/run_meta_qa_online.py` (defaults only)

**Step 1: Write failing policy test/assertion for default evidence roots**

```python
def test_default_evidence_root_uses_tmp_runtime_data():
    from tests.m3_self_development.run_meta_qa_online import DEFAULT_EVIDENCE_ROOT
    assert str(DEFAULT_EVIDENCE_ROOT).startswith("tmp/runtime_data/")
```

**Step 2: Run test to verify current mismatch points fail**

Run: `python3 -m pytest tests/m1-runtime/test_gate_evidence_verifier.py -q`
Expected: FAIL for any default path still under `runtime_data/` (if present).

**Step 3: Update defaults and docs minimally**

```python
DEFAULT_EVIDENCE_ROOT = Path("tmp/runtime_data/execution/evidence/.../")
```

Also update docs language to: runtime evidence defaults to `tmp/runtime_data/...`; repository `runtime_data/` stores templates/index references only.

**Step 4: Re-run focused checks**

Run:
- `python3 tests/m1-runtime/run_post_dev_regression.py --help`
- `python3 tests/m3-self-development/run_meta_qa_online.py --help`

Expected: Help/default text and behavior align with `tmp/runtime_data/...` policy.

**Step 5: Commit**

```bash
git add tests/m1-runtime/TEST.md tests/m3-self-development/TEST.md docs/design/modules/M1-test-system.md docs/architecture/construction_plane.md tests/m1-runtime/run_post_dev_regression.py tests/m3-self-development/run_meta_qa_online.py
git commit -m "docs: align runtime evidence policy to tmp runtime_data defaults"
```

---

### Task 4: Tighten M3 online suite to require representative realistic case assertions

**Files:**
- Modify: `tests/m3-self-development/run_tc_online.py`
- Modify: `tests/m3-self-development/live_cases.md`
- Modify: `tests/m3-self-development/TEST.md`
- Test: `tests/m3-self-development/run_tc_online.py` (CLI execution)

**Step 1: Add failing case assertions in runner logic**

```python
required_assertions = ["happy_path", "failure_path", "rollback_path"]
for key in required_assertions:
    if not case_payload.get("assertions", {}).get(key):
        passed = False
        notes.append(f"missing_required_assertion:{key}")
```

**Step 2: Run targeted suite to verify failure before fix**

Run: `python3 tests/m3-self-development/run_tc_online.py --suite session4-happy`
Expected: FAIL when report lacks required representative assertion set.

**Step 3: Implement minimal report validation adaptation**

```python
def validate_representative_case(report: dict) -> tuple[bool, list[str]]:
    # Ensure fail and rollback evidence exist for admission-grade runs
    ...
```

Integrate this check before case status is marked pass for admission-grade suites.

**Step 4: Re-run online suites**

Run:
- `python3 tests/m3-self-development/run_tc_online.py --suite session4-happy,session4-fail-closed`
- `python3 tests/m3-self-development/run_tc_online.py --suite session6-external`

Expected: PASS only when representative assertions and traceability refs are complete.

**Step 5: Commit**

```bash
git add tests/m3-self-development/run_tc_online.py tests/m3-self-development/live_cases.md tests/m3-self-development/TEST.md
git commit -m "test: require representative realistic assertions for M3 admission suites"
```

---

### Task 5: End-to-end verification and release gate confidence check

**Files:**
- Modify: `docs/review-checklists/` (add checklist item in existing relevant checklist file)
- Reference: `shared/registry/registry_contract_tool.py`

**Step 1: Execute verification commands**

Run:
- `python3 tests/m1-runtime/run_post_dev_regression.py`
- `python3 tests/m3-self-development/run_tc_online.py --suite all`
- `python3 shared/registry/registry_contract_tool.py verify`

Expected:
- M1 regression passes with strict evidence-gate behavior;
- M3 online suite passes only with representative real-chain evidence;
- registry verify passes.

**Step 2: Collect concise verification summary**

```markdown
- Gate authenticity: pass/fail evidence
- tmp evidence policy: validated
- Representative realistic assertions: validated
- Remaining risks: ...
```

**Step 3: Final commit**

```bash
git add docs/review-checklists/*.md
git commit -m "chore: add gate authenticity verification checklist and closure summary"
```

---

## Notes for execution

- Use @superpowers:test-driven-development for each implementation task.
- Use @superpowers:requesting-code-review after each major task block.
- Use @superpowers:verification-before-completion before claiming closure.
- Keep changes minimal (YAGNI): prefer verifier and path policy alignment over broad protocol schema redesign.
