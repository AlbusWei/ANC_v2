# M4/M5 产品化治理（实施层与资产层）Implementation Plan

> Status: Superseded
> Superseded-By: `docs/architecture/` + `docs/design/` + `docs/architecture/construction_plane.md`
> Superseded-On: 2026-03-01

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 M4/M5 从“文档层产品化”推进到“可执行资产层产品化”：落地产品版本实例治理流程、演化闭环流程、对应 runner、测试入口、registry/inventory 联动。

**Architecture:** 以 `ProductVersionInstance`（branch/worktree）作为 M4 生命周期治理对象；在 M5 侧用 `evolution-feedback-planning + evolution-loop` 承载“周期保底 + 事件插队”混合触发。实现遵循最小可执行原则：先改现有 `lifecycle-review` 与 `evolution-feedback-planning`，再补一个可编排的 `evolution-loop` 复合流程，最后接入 M2 回归入口。

**Tech Stack:** Python 3 runner、process.json（P4/P5 manifest）、OpenClaw 分发约束、`shared/registry/*.json`、`tests/m2-bpm-runtime/*` 回归脚本。

---

### Task 1: 为 M4 产品版本实例治理先写失败测试（TDD 起点）

**Files:**
- Create: `tests/m2-bpm-runtime/run_tc_lifecycle_product.py`
- Create: `tests/m2-bpm-runtime/TC-LIFECYCLE-PRODUCT.md`
- Modify: `tests/m2-bpm-runtime/TEST.md`
- Reference: `processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py`

**Step 1: 写失败用例（新字段尚不支持）**

```python
# tests/m2-bpm-runtime/run_tc_lifecycle_product.py
# TC-LIFECYCLE-PROD-001: 目标是 product_version_instance，当前 runner 预期应失败（尚未支持）
request = {
    "final_gate_verdict_ref": "tests/fixtures/quality-gate/sample_pass_verdict.json",
    "target_product_ref": "runtime_data/products/demo-product/product.json",
    "target_version_instance_ref": "runtime_data/products/demo-product/versions/wt-m4m5-v1/version_instance.json",
    "requested_transition": {"from_status": "verify", "to_status": "operate"}
}
assert result["status"] == "failed"
assert "missing_current_status_evidence" in result.get("reason", "")
```

**Step 2: 运行测试确认失败**

Run: `python3 tests/m2-bpm-runtime/run_tc_lifecycle_product.py`
Expected: FAIL（返回码非 0，且理由为未支持产品版本实例输入语义）。

**Step 3: 把测试文档纳入测试挂载**

```markdown
# tests/m2-bpm-runtime/TEST.md 增加
- M4 产品化生命周期套件: `tests/m2-bpm-runtime/run_tc_lifecycle_product.py`
```

**Step 4: 再次运行确认仍失败（红灯）**

Run: `python3 tests/m2-bpm-runtime/run_tc_lifecycle_product.py`
Expected: 仍 FAIL，作为后续实现基线。

**Step 5: Commit**

```bash
git add tests/m2-bpm-runtime/run_tc_lifecycle_product.py tests/m2-bpm-runtime/TC-LIFECYCLE-PRODUCT.md tests/m2-bpm-runtime/TEST.md
git commit -m "test: add failing M4 product-version lifecycle cases"
```

---

### Task 2: 改造 lifecycle-review 为产品版本实例治理流程

**Files:**
- Modify: `processes/meta/lifecycle-review/process.json`
- Modify: `processes/meta/lifecycle-review/SKILL.md`
- Modify: `processes/meta/lifecycle-review/PROCESS.md`
- Modify: `processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py`
- Test: `tests/m2-bpm-runtime/run_tc_lifecycle_product.py`

**Step 1: 扩展输入契约（先让测试继续失败到最小实现）**

```json
// process.json input_contract.required 追加
[
  "final_gate_verdict_ref",
  "target_product_ref",
  "target_version_instance_ref",
  "requested_transition"
]
```

**Step 2: 运行测试确认仍失败（runner 尚未实现）**

Run: `python3 tests/m2-bpm-runtime/run_tc_lifecycle_product.py`
Expected: FAIL（manifest 改了但 runner 尚未识别新字段）。

**Step 3: 在 runner 做最小实现（支持 product/version 语义）**

```python
# lifecycle_review_runner.py 关键最小改造
PRODUCT_INSTANCE_STATES = {"idea","design","build","verify","operate","observe","evolve","deprecate","retire"}
PRODUCT_INSTANCE_TRANSITIONS = {
  "idea": {"design"},
  "design": {"build"},
  "build": {"verify"},
  "verify": {"operate", "deprecate"},
  "operate": {"observe", "evolve", "deprecate"},
  "observe": {"evolve", "deprecate"},
  "evolve": {"design", "build", "verify", "deprecate"},
  "deprecate": {"retire"},
  "retire": set(),
}

def load_version_instance(root: Path, ref: str) -> dict:
    payload = load_json(resolve_path(root, ref))
    if payload.get("entity") != "product_version_instance":
        raise LifecycleReviewError("invalid_version_instance_entity")
    return payload
```

**Step 4: 输出契约追加产品化字段**

```json
{
  "lifecycle_transition_ref": "...",
  "registry_sync_ref": "...",
  "lifecycle_review_report_ref": "...",
  "target_product_id": "demo-product",
  "target_version_instance_id": "wt-m4m5-v1",
  "version_role_tag": "developing"
}
```

**Step 5: 运行测试确认通过**

Run: `python3 tests/m2-bpm-runtime/run_tc_lifecycle_product.py`
Expected: PASS（至少包含一个合法迁移通过 + 一个非法迁移 fail-closed）。

**Step 6: Commit**

```bash
git add processes/meta/lifecycle-review/process.json processes/meta/lifecycle-review/SKILL.md processes/meta/lifecycle-review/PROCESS.md processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py
git commit -m "feat: make lifecycle-review govern product version instances"
```

---

### Task 3: 为 M5 演化提案流程先写失败测试（混合触发）

**Files:**
- Create: `tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py`
- Create: `tests/m2-bpm-runtime/TC-EVOLUTION-FEEDBACK.md`
- Modify: `tests/m2-bpm-runtime/TEST.md`
- Reference: `processes/meta/evolution-feedback-planning/process.json`

**Step 1: 写失败测试（runner 尚不存在）**

```python
# TC-EVO-FEEDBACK-001
request = {
  "trigger_type": "periodic",
  "feedback_evidence_ref": "runtime_data/execution/evidence/bpm-runtime/mock_feedback.json",
  "target_product_ref": "runtime_data/products/demo-product/product.json",
  "target_version_instance_ref": "runtime_data/products/demo-product/versions/wt-m4m5-v1/version_instance.json"
}
# 预期当前失败：runner 不存在或不支持新字段
assert return_code != 0
```

**Step 2: 运行确认失败**

Run: `python3 tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py`
Expected: FAIL（找不到 runner 或输出契约不满足）。

**Step 3: 更新 TEST 挂载**

```markdown
- M5 演化反馈规划套件: `tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py`
```

**Step 4: 再次运行确认红灯**

Run: `python3 tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py`
Expected: FAIL。

**Step 5: Commit**

```bash
git add tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py tests/m2-bpm-runtime/TC-EVOLUTION-FEEDBACK.md tests/m2-bpm-runtime/TEST.md
git commit -m "test: add failing M5 evolution-feedback planning cases"
```

---

### Task 4: 给 evolution-feedback-planning 补可执行 runner 并接入混合触发字段

**Files:**
- Create: `processes/meta/evolution-feedback-planning/scripts/evolution_feedback_planning_runner.py`
- Modify: `processes/meta/evolution-feedback-planning/process.json`
- Modify: `processes/meta/evolution-feedback-planning/SKILL.md`
- Modify: `processes/meta/evolution-feedback-planning/PROCESS.md`
- Test: `tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py`

**Step 1: 扩展 process 输入输出契约（支持 trigger_type + product/version）**

```json
"input_contract": {
  "required": [
    "trigger_type",
    "feedback_evidence_ref",
    "target_product_ref",
    "target_version_instance_ref"
  ]
},
"output_contract": {
  "required": [
    "improvement_plan_ref",
    "retro_report_ref",
    "evolution_proposal_ref"
  ]
}
```

**Step 2: 运行测试确认仍失败（runner 未写）**

Run: `python3 tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py`
Expected: FAIL。

**Step 3: 写最小 runner 实现**

```python
# evolution_feedback_planning_runner.py
ALLOWED_TRIGGER = {"periodic", "event"}
if trigger_type not in ALLOWED_TRIGGER:
    fail_closed("invalid_trigger_type")

proposal = {
  "proposal_id": f"evo-{run_id}",
  "trigger_type": trigger_type,
  "target_product_id": product_payload["product_id"],
  "target_version_instance_id": version_payload["version_instance_id"],
  "expected_value": request.get("expected_value", "TBD"),
  "rollback_plan": request.get("rollback_plan", "fallback_to_previous_active")
}
```

**Step 4: 运行测试确认通过**

Run: `python3 tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py`
Expected: PASS（periodic/event 可通过；非法 trigger fail-closed）。

**Step 5: Commit**

```bash
git add processes/meta/evolution-feedback-planning/scripts/evolution_feedback_planning_runner.py processes/meta/evolution-feedback-planning/process.json processes/meta/evolution-feedback-planning/SKILL.md processes/meta/evolution-feedback-planning/PROCESS.md
git commit -m "feat: add executable M5 evolution feedback planning runner"
```

---

### Task 5: 新增 M5 `evolution-loop` 复合流程资产（承接 M5->M3->M1->M4）

**Files:**
- Create: `processes/meta/evolution-loop/SKILL.md`
- Create: `processes/meta/evolution-loop/PROCESS.md`
- Create: `processes/meta/evolution-loop/process.json`
- Create: `processes/meta/evolution-loop/scripts/evolution_loop_runner.py`
- Modify: `docs/design/processes/p-levels/P3-product-lifecycle-flows.md`
- Test: `tests/m2-bpm-runtime/run_tc_evolution_loop.py` (new)

**Step 1: 写失败测试（流程资产尚不存在）**

```python
# tests/m2-bpm-runtime/run_tc_evolution_loop.py
# TC-EVO-LOOP-001: periodic trigger -> proposal -> implementation_request -> verify_request -> lifecycle_request
assert process_exists is False  # 初次应失败
```

**Step 2: 运行确认失败**

Run: `python3 tests/m2-bpm-runtime/run_tc_evolution_loop.py`
Expected: FAIL（缺少 process assets）。

**Step 3: 写最小 process.json（P4，4 phase）**

```json
"phases": [
  {"phase_id":"p1","name":"proposal","target_id":"process:evolution-feedback-planning"},
  {"phase_id":"p2","name":"implementation-request","target_id":"process:full-development"},
  {"phase_id":"p3","name":"verify-request","target_id":"process:quality-gate-evaluation"},
  {"phase_id":"p4","name":"lifecycle-transition","target_id":"process:lifecycle-review"}
]
```

**Step 4: 写最小 runner（只做编排与证据落盘）**

```python
# evolution_loop_runner.py
# 串联 p1->p4 输入输出引用，不直接实现 M3/M1/M4 细节
# 若任一阶段输出缺失则 fail-closed
```

**Step 5: 运行测试确认通过**

Run: `python3 tests/m2-bpm-runtime/run_tc_evolution_loop.py`
Expected: PASS（最小链路可运行，失败分支能 fail-closed）。

**Step 6: Commit**

```bash
git add processes/meta/evolution-loop/SKILL.md processes/meta/evolution-loop/PROCESS.md processes/meta/evolution-loop/process.json processes/meta/evolution-loop/scripts/evolution_loop_runner.py tests/m2-bpm-runtime/run_tc_evolution_loop.py docs/design/processes/p-levels/P3-product-lifecycle-flows.md
git commit -m "feat: add executable evolution-loop orchestration process"
```

---

### Task 6: 注册新/改流程并同步 inventory（资产层闭环）

**Files:**
- Modify: `shared/registry/process_registry.json`
- Modify: `docs/design/inventories/process-inventory.md`
- Modify: `docs/design/processes/evolution-feedback-planning-process.md` (若不存在则创建)
- Create: `docs/design/processes/evolution-loop-process.md`

**Step 1: 先写校验失败预期（未注册前应失败）**

Run: `python3 shared/registry/registry_contract_tool.py verify`
Expected: 若新增资产未注册则 FAIL。

**Step 2: 注册/升级流程条目**

```json
{
  "process_id": "evolution-feedback-planning",
  "manifest_path": "processes/meta/evolution-feedback-planning/process.json",
  "version": "0.3.0",
  "status": "review"
},
{
  "process_id": "evolution-loop",
  "manifest_path": "processes/meta/evolution-loop/process.json",
  "version": "0.1.0",
  "status": "draft"
}
```

**Step 3: inventory 同步新增 process**

```markdown
- evolution-loop | 复合流程 | draft | processes/meta/evolution-loop/
```

**Step 4: 运行 registry 校验确认通过**

Run: `python3 shared/registry/registry_contract_tool.py verify`
Expected: PASS。

**Step 5: Commit**

```bash
git add shared/registry/process_registry.json docs/design/inventories/process-inventory.md docs/design/processes/evolution-feedback-planning-process.md docs/design/processes/evolution-loop-process.md
git commit -m "chore: register and document M5 executable process assets"
```

---

### Task 7: 接入 M2 回归总入口并完成端到端验收

**Files:**
- Modify: `tests/m2-bpm-runtime/run_post_dev_regression.py`
- Modify: `tests/m2-bpm-runtime/TEST.md`
- Test: `tests/m2-bpm-runtime/run_tc_lifecycle_product.py`
- Test: `tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py`
- Test: `tests/m2-bpm-runtime/run_tc_evolution_loop.py`

**Step 1: 写失败检查（总回归尚未包含新套件）**

Run: `rg -n "lifecycle_product|evolution_feedback|evolution_loop" tests/m2-bpm-runtime/run_post_dev_regression.py`
Expected: 无命中（或缺失）。

**Step 2: 将三套新测试并入回归 suites**

```python
# run_post_dev_regression.py suites 追加
("m4-lifecycle-product", [sys.executable, "tests/m2-bpm-runtime/run_tc_lifecycle_product.py"])
("m5-evolution-feedback", [sys.executable, "tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py"])
("m5-evolution-loop", [sys.executable, "tests/m2-bpm-runtime/run_tc_evolution_loop.py"])
```

**Step 3: 先跑新增三套件**

Run:
- `python3 tests/m2-bpm-runtime/run_tc_lifecycle_product.py`
- `python3 tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py`
- `python3 tests/m2-bpm-runtime/run_tc_evolution_loop.py`

Expected: 全 PASS。

**Step 4: 跑 M2 回归总入口**

Run: `python3 tests/m2-bpm-runtime/run_post_dev_regression.py`
Expected: 新旧套件全部通过；任一失败即 fail-closed。

**Step 5: Commit**

```bash
git add tests/m2-bpm-runtime/run_post_dev_regression.py tests/m2-bpm-runtime/TEST.md tests/m2-bpm-runtime/run_tc_lifecycle_product.py tests/m2-bpm-runtime/run_tc_evolution_feedback_planning.py tests/m2-bpm-runtime/run_tc_evolution_loop.py tests/m2-bpm-runtime/TC-LIFECYCLE-PRODUCT.md tests/m2-bpm-runtime/TC-EVOLUTION-FEEDBACK.md
git commit -m "test: integrate M4/M5 productization suites into M2 regression"
```

---

### Task 8: 文档/模块/施工平面与资产实现对账收口

**Files:**
- Modify: `docs/design/modules/M4-lifecycle-management.md`
- Modify: `docs/design/modules/M5-self-evolution.md`
- Modify: `docs/design/modules/module-dependency-matrix.md`
- Modify: `docs/architecture/construction_plane.md`
- Modify: `docs/design/inventories/process-inventory.md`

**Step 1: 运行对账检查（先看是否缺漏）**

Run: `rg -n "evolution-loop|ProductVersionInstance|run_tc_lifecycle_product|run_tc_evolution_feedback_planning" docs/design docs/architecture`
Expected: 若缺失，先补齐引用。

**Step 2: 补齐实现态条目与状态说明**

```markdown
- M4: lifecycle-review 已支持 product version instance 输入契约。
- M5: evolution-feedback-planning 已有执行 runner；evolution-loop 已落地。
- 回归入口: tests/m2-bpm-runtime/run_post_dev_regression.py 已接入。
```

**Step 3: 跑最终门禁**

Run:
- `python3 shared/registry/registry_contract_tool.py verify`
- `openspec validate --all`

Expected: 全 PASS。

**Step 4: Commit**

```bash
git add docs/design/modules/M4-lifecycle-management.md docs/design/modules/M5-self-evolution.md docs/design/modules/module-dependency-matrix.md docs/architecture/construction_plane.md docs/design/inventories/process-inventory.md
git commit -m "docs: close implementation alignment for M4/M5 productized assets"
```
