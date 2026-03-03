# M1/M3 + M4/M5 Executable Gap Closure Implementation Plan

> Status: Superseded
> Superseded-By: `docs/architecture/` + `docs/design/` + `docs/architecture/construction_plane.md`
> Superseded-On: 2026-03-01

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 M1/M3 的真实性门禁与 M4/M5 产品化治理从“文档语义”升级为“可执行、可验证、可追溯”的最小运行闭环。

**Architecture:** 先在 M1 gate 聚合点建立集中证据链校验（P0），确保 simulated/skeleton 不能进入准入结论；再在 M4 增加 ProductVersionInstance 治理执行器（P1），并在 M5 增加混合触发提案执行器（P2）；最后通过 M5→M3→M1→M4 的最小端到端 smoke（P3）验证联通。保持 registry 资产五态兼容，不做重型 schema 重构。

**Tech Stack:** Python 3, pytest, existing M1/M3 runners, JSON evidence artifacts, OpenSpec/registry verification CLI, Markdown docs.

---

### Task 1: 为 M1 证据链校验补齐失败优先测试

**Files:**
- Create: `tests/m1-runtime/test_gate_evidence_verifier.py`
- Modify: `tests/m1-runtime/TEST.md`
- Reference: `processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py`

**Step 1: 写第一个失败测试（缺 openclaw trace）**

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

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/m1-runtime/test_gate_evidence_verifier.py::test_gate_fails_without_openclaw_trace -q`
Expected: FAIL（`verify_gate_evidence_chain` 未定义）。

**Step 3: 增加两个失败场景测试（缺 phase output / case 非代表性）**

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


def test_gate_fails_when_case_report_not_representative(tmp_path: Path):
    payload = {
        "dispatch_trace_ref": "tmp/runtime_data/evidence/dispatch.json",
        "phase_outputs": ["tmp/runtime_data/evidence/p1.json"],
        "case_report_ref": "tmp/runtime_data/evidence/case_report.json",
    }
    ok, reason = verify_gate_evidence_chain(payload, repo_root=tmp_path)
    assert ok is False
    assert reason == "case_report_not_representative"
```

**Step 4: 运行测试确认全部失败（红灯基线）**

Run: `python3 -m pytest tests/m1-runtime/test_gate_evidence_verifier.py -q`
Expected: FAIL（函数缺失或行为不满足）。

**Step 5: Commit**

```bash
git add tests/m1-runtime/test_gate_evidence_verifier.py tests/m1-runtime/TEST.md
git commit -m "test(m1): add failing evidence-chain verifier test baseline"
```

---

### Task 2: 在质量门禁聚合点实现集中证据链校验并强制生效

**Files:**
- Modify: `processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py`
- Modify: `tests/fixtures/quality-gate/aggregation_rules.json`
- Test: `tests/m1-runtime/test_gate_evidence_verifier.py`

**Step 1: 写最小实现函数**

```python
def verify_gate_evidence_chain(payload: dict, repo_root: Path) -> tuple[bool, str]:
    dispatch_ref = str(payload.get("dispatch_trace_ref") or "").strip()
    if not dispatch_ref or not resolve_path(repo_root, dispatch_ref).exists():
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
    if not isinstance(assertions, dict) or not assertions.get("failure_path") or not assertions.get("rollback_path"):
        return False, "case_report_not_representative"

    return True, "ok"
```

**Step 2: 在 gate 判定前强制调用 verifier**

```python
verified, verify_reason = verify_gate_evidence_chain(
    {
        "dispatch_trace_ref": p4_dispatch.get("dispatch_output_ref", ""),
        "phase_outputs": [objective_eval_ref, regression_eval_ref, final_gate_verdict_ref],
        "case_report_ref": str(request.get("case_report_ref") or ""),
    },
    repo_root=root,
)
if not verified:
    gate_decision = "fail"
    runtime_gate_state = "fail"
    phase_trace.append({
        "phase": "evidence-verification",
        "status": "failed",
        "reason": verify_reason,
        "ts": now_iso(),
    })
```

**Step 3: 运行单测确认转绿**

Run: `python3 -m pytest tests/m1-runtime/test_gate_evidence_verifier.py -q`
Expected: PASS。

**Step 4: 运行 M1 回归 smoke**

Run: `python3 tests/m1-runtime/run_post_dev_regression.py`
Expected: pass/fail-closed/hold 套件仍可执行，且缺证据时不出现误 pass。

**Step 5: Commit**

```bash
git add processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py tests/fixtures/quality-gate/aggregation_rules.json tests/m1-runtime/test_gate_evidence_verifier.py
git commit -m "feat(m1): enforce centralized evidence-chain verification in gate admission"
```

---

### Task 3: 统一 M1/M3 默认证据根到 tmp/runtime_data

**Files:**
- Modify: `tests/m1-runtime/run_post_dev_regression.py`
- Modify: `tests/m3-self-development/run_meta_qa_online.py`
- Modify: `tests/m1-runtime/TEST.md`
- Modify: `tests/m3-self-development/TEST.md`
- Modify: `docs/design/modules/M1-test-system.md`
- Modify: `docs/architecture/construction_plane.md`

**Step 1: 写失败测试（默认路径策略）**

```python
from tests.m3_self_development.run_meta_qa_online import DEFAULT_EVIDENCE_ROOT

def test_meta_qa_default_evidence_root_uses_tmp_runtime_data():
    assert str(DEFAULT_EVIDENCE_ROOT).startswith("tmp/runtime_data/")
```

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/m1-runtime/test_gate_evidence_verifier.py -q`
Expected: FAIL（当前默认值仍为 `runtime_data/...`）。

**Step 3: 最小改动实现路径统一**

```python
DEFAULT_EVIDENCE_ROOT = Path("tmp/runtime_data/execution/evidence/self-development/runtime-validation-round-meta-assets/latest")
```

并把 `run_post_dev_regression.py` 的 `--evidence-root` 默认值切到 `tmp/runtime_data/...`。

**Step 4: 运行帮助与冒烟检查**

Run:
- `python3 tests/m1-runtime/run_post_dev_regression.py --help`
- `python3 tests/m3-self-development/run_meta_qa_online.py --help`

Expected: 默认路径文案与行为均指向 `tmp/runtime_data/...`。

**Step 5: Commit**

```bash
git add tests/m1-runtime/run_post_dev_regression.py tests/m3-self-development/run_meta_qa_online.py tests/m1-runtime/TEST.md tests/m3-self-development/TEST.md docs/design/modules/M1-test-system.md docs/architecture/construction_plane.md
git commit -m "chore(runtime): unify default evidence root to tmp/runtime_data"
```

---

### Task 4: 为 M4 新增 ProductVersionInstance 最小治理执行器

**Files:**
- Create: `processes/meta/lifecycle-review/scripts/product_lifecycle_governance_runner.py`
- Create: `tests/m4-lifecycle/test_product_lifecycle_governance_runner.py`
- Modify: `processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py`
- Modify: `docs/design/modules/M4-lifecycle-management.md`

**Step 1: 写失败测试（状态迁移 + 角色切换证据约束）**

```python
def test_transition_fails_without_required_product_fields(tmp_path):
    payload = {
        "product": {"product_id": "p1"},
        "version_instance": {"branch_or_worktree_id": "wt-a", "state": "design"},
        "transition": {"to_state": "verify"},
    }
    code, out = run_governance(payload, tmp_path)
    assert code == 2
    assert out["reason"] == "missing_product_contract_fields"


def test_switch_role_fails_without_verification_and_rollback(tmp_path):
    payload = {
        "product": {
            "product_id": "p1",
            "goal": "g",
            "consumer": "c",
            "scope": "s",
            "acceptance": "a",
            "version_policy": "vp",
        },
        "version_instance": {
            "product_id": "p1",
            "branch_or_worktree_id": "wt-a",
            "state": "verify",
            "role_tag": "developing",
        },
        "role_switch": {"to_role": "active"},
    }
    code, out = run_governance(payload, tmp_path)
    assert code == 2
    assert out["reason"] == "missing_role_switch_evidence"
```

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/m4-lifecycle/test_product_lifecycle_governance_runner.py -q`
Expected: FAIL（runner 未实现）。

**Step 3: 写最小执行器实现**

```python
REQUIRED_PRODUCT_FIELDS = ["product_id", "goal", "consumer", "scope", "acceptance", "version_policy"]


def validate_product_contract(product: dict) -> tuple[bool, str]:
    for key in REQUIRED_PRODUCT_FIELDS:
        if not str(product.get(key) or "").strip():
            return False, "missing_product_contract_fields"
    return True, "ok"


def switch_version_role(req: dict) -> tuple[bool, str]:
    if not req.get("verification_ref") or not req.get("rollback_plan_ref"):
        return False, "missing_role_switch_evidence"
    return True, "ok"
```

**Step 4: 再跑测试确认通过**

Run: `python3 -m pytest tests/m4-lifecycle/test_product_lifecycle_governance_runner.py -q`
Expected: PASS。

**Step 5: Commit**

```bash
git add processes/meta/lifecycle-review/scripts/product_lifecycle_governance_runner.py tests/m4-lifecycle/test_product_lifecycle_governance_runner.py processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py docs/design/modules/M4-lifecycle-management.md
git commit -m "feat(m4): add product version governance runner with fail-closed checks"
```

---

### Task 5: 为 M5 新增混合触发提案执行器并编排到 M3/M1/M4

**Files:**
- Create: `processes/meta/self-evolution/scripts/evolution_proposal_runner.py`
- Create: `tests/m5-self-evolution/test_evolution_proposal_runner.py`
- Modify: `docs/design/modules/M5-self-evolution.md`
- Modify: `docs/design/interfaces/product-lifecycle-governance-protocol.md`

**Step 1: 写失败测试（触发类型与回滚约束）**

```python
def test_submit_proposal_fails_when_trigger_type_invalid(tmp_path):
    payload = {"proposal_id": "ep-1", "trigger_type": "manual", "target_product_id": "p1"}
    code, out = run_proposal(payload, tmp_path)
    assert code == 2
    assert out["reason"] == "invalid_trigger_type"


def test_submit_proposal_fails_without_rollback_plan(tmp_path):
    payload = {
        "proposal_id": "ep-1",
        "trigger_type": "event",
        "target_product_id": "p1",
        "expected_value": "reduce_fail_rate",
        "verification_metrics": ["gate_pass_rate"],
    }
    code, out = run_proposal(payload, tmp_path)
    assert code == 2
    assert out["reason"] == "missing_rollback_plan"
```

**Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/m5-self-evolution/test_evolution_proposal_runner.py -q`
Expected: FAIL。

**Step 3: 最小实现提案 + 编排骨架**

```python
if trigger_type not in {"periodic", "event"}:
    return fail_closed("invalid_trigger_type")
if not rollback_plan:
    return fail_closed("missing_rollback_plan")

pipeline = ["M3 Implement", "M1 Verify", "M4 Transition"]
```

在输出中写入：`m3_execution_ref`、`m1_verification_ref`、`m4_transition_ref`（无 ref 则 fail）。

**Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/m5-self-evolution/test_evolution_proposal_runner.py -q`
Expected: PASS。

**Step 5: Commit**

```bash
git add processes/meta/self-evolution/scripts/evolution_proposal_runner.py tests/m5-self-evolution/test_evolution_proposal_runner.py docs/design/modules/M5-self-evolution.md docs/design/interfaces/product-lifecycle-governance-protocol.md
git commit -m "feat(m5): add hybrid-trigger evolution proposal runner and orchestration refs"
```

---

### Task 6: 新增 M5→M3→M1→M4 端到端 smoke（主链 + fail-closed）

**Files:**
- Create: `tests/m5-self-evolution/run_productized_e2e_smoke.py`
- Create: `tests/m5-self-evolution/fixtures/proposal_event_minimal.json`
- Create: `tests/m5-self-evolution/fixtures/proposal_missing_rollback.json`
- Modify: `tests/m5-self-evolution/TEST.md`
- Modify: `docs/architecture/construction_plane.md`

**Step 1: 写失败测试（先红灯）**

```python
def test_e2e_event_proposal_path_passes_when_all_refs_present():
    rc = run_case("proposal_event_minimal.json")
    assert rc == 0


def test_e2e_event_proposal_fail_closed_without_rollback():
    rc = run_case("proposal_missing_rollback.json")
    assert rc == 2
```

**Step 2: 运行确认失败**

Run: `python3 -m pytest tests/m5-self-evolution -q`
Expected: FAIL（smoke runner 未完成）。

**Step 3: 实现 smoke runner 最小串联**

```python
# 1) 调 evolution_proposal_runner 产 proposal
# 2) 调 m3 runner 产 execution ref
# 3) 调 m1 gate runner 产 verification ref
# 4) 调 m4 governance runner 产 transition ref
# 任一环节缺 ref => return 2
```

**Step 4: 运行 smoke 与测试**

Run:
- `python3 tests/m5-self-evolution/run_productized_e2e_smoke.py --case proposal_event_minimal`
- `python3 tests/m5-self-evolution/run_productized_e2e_smoke.py --case proposal_missing_rollback`
- `python3 -m pytest tests/m5-self-evolution -q`

Expected:
- 主链 case 返回 0
- 缺 rollback case 返回 2
- pytest PASS

**Step 5: Commit**

```bash
git add tests/m5-self-evolution/run_productized_e2e_smoke.py tests/m5-self-evolution/fixtures/proposal_event_minimal.json tests/m5-self-evolution/fixtures/proposal_missing_rollback.json tests/m5-self-evolution/TEST.md docs/architecture/construction_plane.md
git commit -m "test(e2e): add productized evolution-to-governance smoke suite"
```

---

### Task 7: 全链验证与准入总结

**Files:**
- Modify: `docs/review-checklists/`（在已有相关 checklist 文件补充条目）
- Modify: `docs/architecture/construction_plane.md`
- Validate: `shared/registry/registry_contract_tool.py`

**Step 1: 执行全链验证命令**

Run:
- `python3 -m pytest tests/m1-runtime/test_gate_evidence_verifier.py -q`
- `python3 -m pytest tests/m4-lifecycle/test_product_lifecycle_governance_runner.py -q`
- `python3 -m pytest tests/m5-self-evolution/test_evolution_proposal_runner.py -q`
- `python3 tests/m5-self-evolution/run_productized_e2e_smoke.py --case proposal_event_minimal`
- `python3 tests/m5-self-evolution/run_productized_e2e_smoke.py --case proposal_missing_rollback`
- `python3 shared/registry/registry_contract_tool.py verify`
- `openspec validate --all`

Expected:
- 真实性门禁测试通过；
- M4/M5 最小执行层测试通过；
- E2E 主链 + fail-closed 链路行为符合预期；
- registry 与 openspec 校验通过。

**Step 2: 产出自然语言验收结论**

```markdown
- 目标达成度：...
- 准入真实性：...
- M4/M5 runtime 化状态：...
- fail-closed 覆盖：...
- 残余风险与下一步：...
```

**Step 3: Commit**

```bash
git add docs/review-checklists/*.md docs/architecture/construction_plane.md
git commit -m "chore(closure): add executable gap closure verification summary"
```

---

## Execution Notes

- 每个实现任务先走失败测试，再补最小实现（严格 TDD）。
- 每个 task 完成后使用 `@superpowers:requesting-code-review` 做块级审查。
- 宣告完成前使用 `@superpowers:verification-before-completion`。
- 保持 YAGNI：仅实现最小闭环，不提前引入复杂调度/持久化基础设施。
