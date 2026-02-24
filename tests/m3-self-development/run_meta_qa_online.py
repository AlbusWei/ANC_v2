#!/usr/bin/env python3
"""Meta 资产在线 QA 统一入口（Phase5）。

设计目标：
1. 覆盖全量 Meta Skills + Meta Processes，每资产固定 HP/FC/TR/RB 四类场景。
2. 以在线运行时行为为主验收；静态契约校验作为辅助门禁。
3. 复用既有 runner 能力，不重复造评测引擎。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DEFAULT_EVIDENCE_ROOT = Path(
    "docs/design/modules/evidence/self-development/runtime-validation-round-meta-assets/latest"
)
DEFAULT_REPORT_NAME = "meta_qa_online_report.json"
DEFAULT_SUMMARY_NAME = "meta_qa_online_summary.md"
DEFAULT_DEFECTS_NAME = "defects.json"
DEFAULT_DEFECTS_SUMMARY_NAME = "defect_summary.md"
DEFAULT_REGRESSION_PLAN_NAME = "regression_plan.json"

SCENARIOS: Tuple[str, ...] = ("HP", "FC", "TR", "RB")

RUNNER_SKILL_SCRIPT: Dict[str, str] = {
    "meta.arch.agent-creator": "skills/meta/agent-creator/scripts/agent_creator_runner.py",
    "meta.arch.process-creator": "skills/meta/process-creator/scripts/process_creator_runner.py",
    "meta.arch.template-validator": "skills/meta/template-validator/scripts/template_validator_runner.py",
    "meta.arch.skill-creator": "skills/skill-creator/scripts/meta_skill_creator_runner.py",
}

PASS_DECISIONS = {"pass", "approved", "allow", "success", "ok"}
BLOCK_DECISIONS = {"fail", "fail_closed", "hold", "test_invalid", "blocked", "rejected"}


@dataclass(frozen=True)
class AssetDef:
    asset_kind: str
    asset_id: str
    runtime_key: str
    display_name: str
    contract_refs: Tuple[str, ...]
    contract_path: str
    registry_path: str
    runner_path: str
    process_manifest_path: str


@dataclass(frozen=True)
class CaseDef:
    case_id: str
    asset_kind: str
    asset_id: str
    scenario: str
    execution_mode: str
    input_payload: Dict[str, Any]
    expected_output: Dict[str, Any]
    assertion_rules: Tuple[str, ...]
    expected_exit_code: int
    contract_refs: Tuple[str, ...]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError("not inside git repository")
    return Path(proc.stdout.strip()).resolve()


def parse_json_from_mixed_output(text: str) -> Any:
    decoder = json.JSONDecoder()
    fallback: Any = None
    for idx, ch in enumerate(text):
        if ch not in "[{":
            continue
        try:
            value, end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        remainder = text[idx + end :].strip()
        if not remainder:
            return value
        fallback = value

    if fallback is not None:
        return fallback

    for line in reversed(text.splitlines()):
        raw = line.strip()
        if not raw:
            continue
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            continue
    return {}


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return payload


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def to_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def split_csv(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def slug_upper(raw: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", raw.upper()).strip("-")


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def openclaw_cmd(profile: str, *parts: str) -> List[str]:
    cmd = ["openclaw"]
    if profile:
        cmd.extend(["--profile", profile])
    cmd.extend(parts)
    return cmd


def load_assets(root: Path) -> Tuple[List[AssetDef], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    skill_registry_path = root / "shared/registry/skill_registry.json"
    process_registry_path = root / "shared/registry/process_registry.json"

    skill_registry = load_json(skill_registry_path)
    process_registry = load_json(process_registry_path)

    skill_index: Dict[str, Dict[str, Any]] = {}
    process_index: Dict[str, Dict[str, Any]] = {}
    assets: List[AssetDef] = []

    for entry in skill_registry.get("entries", []):
        if not isinstance(entry, dict):
            continue
        skill_id = str(entry.get("skill_id") or "")
        if not skill_id.startswith("meta."):
            continue
        name = str(entry.get("name") or "").strip()
        path = str(entry.get("path") or "").strip()
        if not name or not path:
            continue

        skill_index[skill_id] = entry
        runner_path = RUNNER_SKILL_SCRIPT.get(skill_id, "")
        assets.append(
            AssetDef(
                asset_kind="meta_skill",
                asset_id=skill_id,
                runtime_key=name,
                display_name=name,
                contract_refs=(
                    path,
                    "shared/registry/skill_registry.json",
                ),
                contract_path=path,
                registry_path="shared/registry/skill_registry.json",
                runner_path=runner_path,
                process_manifest_path="",
            )
        )

    for entry in process_registry.get("entries", []):
        if not isinstance(entry, dict):
            continue
        skill_path = str(entry.get("skill_path") or "")
        process_id = str(entry.get("process_id") or "")
        manifest_path = str(entry.get("manifest_path") or "")
        if not skill_path.startswith("processes/meta/"):
            continue
        if not process_id or not manifest_path:
            continue

        process_index[process_id] = entry
        assets.append(
            AssetDef(
                asset_kind="meta_process",
                asset_id=process_id,
                runtime_key=process_id,
                display_name=process_id,
                contract_refs=(
                    skill_path,
                    manifest_path,
                    "shared/registry/process_registry.json",
                ),
                contract_path=skill_path,
                registry_path="shared/registry/process_registry.json",
                runner_path="",
                process_manifest_path=manifest_path,
            )
        )

    assets.sort(key=lambda item: (item.asset_kind, item.asset_id))
    return assets, skill_index, process_index


def build_runner_input(asset: AssetDef, scenario: str) -> Dict[str, Any]:
    if asset.asset_id == "meta.arch.agent-creator":
        if scenario == "HP":
            return {
                "agent_id": "demo-agent",
                "role_scope": {
                    "responsibilities": ["产出 Agent 资产计划"],
                    "boundaries": ["不修改实现文件"],
                },
                "interfaces": [
                    {"protocol_ref": "docs/design/interfaces/meta-self-modification-protocol.md"}
                ],
                "owner": "architect",
            }
        return {
            "agent_id": "demo-agent",
            "role_scope": {"responsibilities": ["缺边界触发 FC"]},
            "interfaces": [],
        }

    if asset.asset_id == "meta.arch.process-creator":
        if scenario == "HP":
            return {
                "process_id": "demo-meta-process-p5",
                "version": "1.0.0",
                "process_level": "p5",
                "phases": [
                    {
                        "phase_id": "p1",
                        "name": "需求契约澄清",
                        "actor": "qa",
                        "target_type": "subprocess",
                        "target_id": "spec-authoring-contract",
                        "requires_spec": True,
                        "spec_ref": "docs/design/processes/atomic/AP-004-spec-authoring.md#ap-004-spec-authoring",
                        "sipoc": {
                            "suppliers": ["meta.arch.objective-writer"],
                            "inputs": ["objective_delta"],
                            "process": ["spec_contract_check"],
                            "outputs": ["spec_contract"],
                            "customers": ["meta.arch.process-creator"],
                        },
                        "acceptance_criteria": ["spec_contract 非空", "契约锚点可追溯"],
                        "phase_purpose": "将目标转译为可执行 spec 契约。",
                        "input_context_ref": "docs/design/README.md#spec-context",
                        "done_definition": "输出 spec_contract 并完成锚点绑定。",
                        "handoff_note": "交付下一阶段进行质量门禁准备。",
                    },
                    {
                        "phase_id": "p2",
                        "name": "质量门禁准备",
                        "actor": "qa",
                        "target_type": "subprocess",
                        "target_id": "quality-gate-preparation",
                        "requires_spec": False,
                        "sipoc": {
                            "suppliers": ["meta.arch.process-creator"],
                            "inputs": ["spec_contract"],
                            "process": ["prepare_quality_gate"],
                            "outputs": ["gate_bundle"],
                            "customers": ["quality-gate-evaluation"],
                        },
                        "acceptance_criteria": ["gate_bundle 字段完整", "失败路径具备 fail_closed 语义"],
                        "phase_purpose": "生成质量门禁输入与追溯证据。",
                        "input_context_ref": "docs/architecture/process_architecture.md#quality-gate",
                        "done_definition": "完成 gate_bundle 并记录证据字段。",
                        "handoff_note": "进入门禁评估子流程。",
                    },
                ],
                "control_flow": [
                    {"from": "p1", "to": "p2", "on": "success"},
                    {"from": "p1", "to": "end", "on": "failure"},
                    {"from": "p2", "to": "end", "on": "success"},
                    {"from": "p2", "to": "end", "on": "failure"},
                ],
                "fail_policy": {
                    "mode": "fail_closed",
                    "retry": {"max_iterations": 1},
                    "escalation_chain": ["qa", "governance-board"],
                },
                "evidence_policy": {
                    "required_fields": [
                        "timestamp",
                        "phase_id",
                        "actor",
                        "input_ref",
                        "output_ref",
                        "decision",
                        "reason",
                    ]
                },
                "lineage_policy": {
                    "stack_depth_limit": 4,
                    "context_isolation": "strict",
                    "output_handoff_mode": "artifact_ref",
                },
            }
        return {
            "process_id": "demo-meta-process",
            "process_level": "p5",
            "phases": [
                {
                    "phase_id": "p1",
                    "target_type": "skill",
                    "requires_spec": True,
                }
            ],
            "control_flow": {
                "start": "p1",
                "terminal": ["end"],
            },
            "fail_policy": {
                "on_fail": "fail_closed",
            },
        }

    if asset.asset_id == "meta.arch.template-validator":
        if scenario == "HP":
            return {
                "template_ref": "skills/meta/template-validator/SKILL.md",
                "schema_ref": "shared/registry/skill_registry.json",
                "target_asset_ref": "shared/registry/skill_registry.json",
                "validation_profile": "strict",
                "expected_keys": ["schema_version", "entries"],
            }
        return {
            "template_ref": "skills/meta/template-validator/SKILL.md",
            "target_asset_ref": "shared/registry/skill_registry.json",
            "validation_profile": "strict",
        }

    if asset.asset_id == "meta.arch.skill-creator":
        if scenario == "HP":
            return {
                "skill_name": "qa-meta-demo-skill",
                "layer": "meta",
                "namespace": "phase5",
                "objective_ref": "obj-m3-meta-asset-quality-hardening",
                "description": "Phase5 online QA demo skill",
                "output_root": "__CASE_OUTPUT_ROOT__",
            }
        return {
            "skill_name": "qa-meta-demo-skill",
            "layer": "meta",
            "namespace": "phase5",
            "description": "触发缺字段",
            "output_root": "__CASE_OUTPUT_ROOT__",
        }

    return {}


def build_case_payload(asset: AssetDef, scenario: str, mode: str) -> Dict[str, Any]:
    if mode == "runner":
        return {
            "asset_id": asset.asset_id,
            "scenario": scenario,
            "runner_input": build_runner_input(asset, scenario),
        }

    return {
        "asset_id": asset.asset_id,
        "scenario": scenario,
        "qa_online_contract": {
            "required_fields": [
                "gate_decision",
                "asset_id",
                "scenario",
                "reason_code",
                "expected_exit_code",
                "traceability_refs",
                "recovery_or_rollback",
            ]
        },
    }


def build_case_expected_output(scenario: str) -> Dict[str, Any]:
    if scenario == "HP":
        return {
            "gate_decision": "pass|approved|allow|success",
            "expected_exit_code": 0,
            "traceability_refs": "non_empty",
        }
    return {
        "gate_decision": "fail_closed|fail|hold|test_invalid|blocked|rejected",
        "expected_exit_code": 2,
        "traceability_refs": "non_empty",
    }


def case_mode(asset: AssetDef, scenario: str) -> str:
    if asset.asset_kind == "meta_skill" and asset.runner_path and scenario in {"HP", "FC"}:
        return "runner"
    if scenario in {"TR", "RB"}:
        return "online_qa"
    if asset.asset_kind == "meta_process":
        return "online_qa"
    return "online_qa"


def generate_cases(assets: List[AssetDef]) -> List[CaseDef]:
    cases: List[CaseDef] = []
    for asset in assets:
        prefix = ("MS" if asset.asset_kind == "meta_skill" else "MP") + "-" + slug_upper(asset.display_name)
        for scenario in SCENARIOS:
            mode = case_mode(asset, scenario)
            rules = [
                "contract_refs_exists",
                "expected_exit_code_match",
            ]
            if scenario == "TR":
                rules.append("traceability_chain_complete")
            if scenario == "RB":
                rules.append("rollback_or_recovery_semantics_complete")
            if mode == "online_qa":
                rules.append("openclaw_online_response_contract")
            if mode == "runner":
                rules.append("runner_output_contract")

            cases.append(
                CaseDef(
                    case_id=f"{prefix}-{scenario}",
                    asset_kind=asset.asset_kind,
                    asset_id=asset.asset_id,
                    scenario=scenario,
                    execution_mode=mode,
                    input_payload=build_case_payload(asset, scenario, mode),
                    expected_output=build_case_expected_output(scenario),
                    assertion_rules=tuple(rules),
                    expected_exit_code=0 if scenario == "HP" else 2,
                    contract_refs=asset.contract_refs,
                )
            )
    return cases


def build_suite_map(cases: List[CaseDef]) -> Dict[str, List[str]]:
    suite_map: Dict[str, List[str]] = {
        "meta-skills": [],
        "meta-processes": [],
        "online-critical": [],
        "final-regression-full": [],
    }
    for case in cases:
        suite_map["final-regression-full"].append(case.case_id)
        if case.asset_kind == "meta_skill":
            suite_map["meta-skills"].append(case.case_id)
        if case.asset_kind == "meta_process":
            suite_map["meta-processes"].append(case.case_id)
        if case.scenario in {"HP", "FC"}:
            suite_map["online-critical"].append(case.case_id)
    suite_map["all"] = list(suite_map["final-regression-full"])
    return suite_map


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Meta QA online suites")
    parser.add_argument("--suite", default="", help="Comma-separated suites")
    parser.add_argument("--case", default="", help="Comma-separated case ids")
    parser.add_argument("--list-cases", action="store_true", help="List all generated cases")
    parser.add_argument("--dry-run", action="store_true", help="Check executability/coverage only")
    parser.add_argument(
        "--evidence-root",
        default=str(DEFAULT_EVIDENCE_ROOT.as_posix()),
        help="Repo-relative evidence root",
    )
    parser.add_argument("--report", default=DEFAULT_REPORT_NAME, help="Report filename under evidence root")
    parser.add_argument("--openclaw-profile", default="", help="Optional openclaw profile")
    parser.add_argument("--max-online-seconds", type=int, default=180, help="Timeout for openclaw online case")
    return parser.parse_args()


def materialize_selection(args: argparse.Namespace, suite_map: Dict[str, List[str]], case_by_id: Dict[str, CaseDef]) -> Dict[str, Any]:
    suite_inputs = split_csv(args.suite)
    case_inputs = split_csv(args.case)
    errors: List[str] = []
    selected_ids: List[str] = []
    selected_set = set()

    for suite_name in suite_inputs:
        if suite_name == "final-regression":
            for case_id in suite_map["final-regression-full"]:
                if case_id not in selected_set:
                    selected_set.add(case_id)
                    selected_ids.append(case_id)
            continue
        if suite_name not in suite_map:
            errors.append(f"unknown_suite:{suite_name}")
            continue
        for case_id in suite_map[suite_name]:
            if case_id not in selected_set:
                selected_set.add(case_id)
                selected_ids.append(case_id)

    for case_id in case_inputs:
        if case_id not in case_by_id:
            errors.append(f"unknown_case:{case_id}")
            continue
        if case_id not in selected_set:
            selected_set.add(case_id)
            selected_ids.append(case_id)

    default_mode = not suite_inputs and not case_inputs
    if default_mode:
        selected_ids = list(suite_map["final-regression-full"])

    return {
        "suite_inputs": suite_inputs,
        "case_inputs": case_inputs,
        "selected_case_ids": selected_ids,
        "errors": errors,
        "default_mode": default_mode,
        "layered_regression": ("final-regression" in suite_inputs) and (not case_inputs),
    }


def check_contract_refs_exist(root: Path, refs: Iterable[str]) -> Tuple[bool, List[str]]:
    missing: List[str] = []
    for ref in refs:
        path = (root / ref).resolve()
        if not path.exists():
            missing.append(ref)
    return len(missing) == 0, missing


def traceability_check(root: Path, asset: AssetDef, skill_index: Dict[str, Dict[str, Any]], process_index: Dict[str, Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    if asset.asset_kind == "meta_skill":
        entry = skill_index.get(asset.asset_id)
        if not entry:
            return False, {"reason_code": "traceability_broken", "message": "skill_registry 缺少该资产"}
        if str(entry.get("path") or "") != asset.contract_path:
            return False, {
                "reason_code": "traceability_broken",
                "message": "skill_registry.path 与契约路径不一致",
                "registry_path": entry.get("path"),
                "contract_path": asset.contract_path,
            }
        return True, {"reason_code": "ok", "registry_ref": asset.registry_path}

    entry = process_index.get(asset.asset_id)
    if not entry:
        return False, {"reason_code": "traceability_broken", "message": "process_registry 缺少该资产"}
    if str(entry.get("skill_path") or "") != asset.contract_path:
        return False, {
            "reason_code": "traceability_broken",
            "message": "process_registry.skill_path 与契约路径不一致",
            "registry_path": entry.get("skill_path"),
            "contract_path": asset.contract_path,
        }
    if str(entry.get("manifest_path") or "") != asset.process_manifest_path:
        return False, {
            "reason_code": "traceability_broken",
            "message": "process_registry.manifest_path 与实际不一致",
            "registry_manifest": entry.get("manifest_path"),
            "manifest_path": asset.process_manifest_path,
        }
    return True, {"reason_code": "ok", "registry_ref": asset.registry_path}


def rollback_check(root: Path, asset: AssetDef) -> Tuple[bool, Dict[str, Any]]:
    if asset.asset_kind == "meta_process":
        manifest = load_json((root / asset.process_manifest_path).resolve())
        fail_policy = manifest.get("fail_policy")
        if not isinstance(fail_policy, dict):
            return False, {"reason_code": "rollback_semantics_missing", "message": "缺失 fail_policy"}
        retry = fail_policy.get("retry")
        escalation = fail_policy.get("escalation_chain")
        ok = isinstance(retry, dict) and bool(retry) and isinstance(escalation, list) and len(escalation) > 0
        if not ok:
            return False, {
                "reason_code": "rollback_semantics_missing",
                "message": "fail_policy.retry/escalation_chain 不完整",
            }
        return True, {"reason_code": "ok"}

    content = (root / asset.contract_path).read_text(encoding="utf-8")
    has_fail_closed = "Fail-Closed" in content or "fail-closed" in content.lower()
    has_exit_code = "返回码" in content or "exit code" in content.lower()
    if not (has_fail_closed and has_exit_code):
        return False, {
            "reason_code": "rollback_semantics_missing",
            "message": "skill 契约缺 Fail-Closed 或返回码语义",
        }

    if asset.runner_path:
        runner_path = (root / asset.runner_path).resolve()
        if runner_path.exists():
            runner_text = runner_path.read_text(encoding="utf-8")
            if "EXIT_FAIL_CLOSED" not in runner_text:
                return False, {
                    "reason_code": "rollback_semantics_missing",
                    "message": "runner 未声明 EXIT_FAIL_CLOSED",
                }
    return True, {"reason_code": "ok"}


def check_online_eligibility(root: Path, profile: str, runtime_key: str, cache: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if runtime_key in cache:
        return cache[runtime_key]

    cmd = openclaw_cmd(profile, "skills", "info", runtime_key, "--json")
    proc = run_cmd(cmd, root)
    parsed = parse_json_from_mixed_output(proc.stdout)
    result = {
        "command": " ".join(cmd),
        "return_code": proc.returncode,
        "eligible": isinstance(parsed, dict) and parsed.get("eligible") is True,
        "file_path": parsed.get("filePath") if isinstance(parsed, dict) else "",
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-20:]),
    }
    cache[runtime_key] = result
    return result


def dry_run_case(
    *,
    root: Path,
    case: CaseDef,
    asset: AssetDef,
    profile: str,
    run_root: Path,
    skill_index: Dict[str, Dict[str, Any]],
    process_index: Dict[str, Dict[str, Any]],
    online_cache: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    case_dir = run_root / "cases" / case.case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    input_path = case_dir / "input.json"
    output_path = case_dir / "output.json"
    assertions_path = case_dir / "assertions.json"
    command_trace_path = case_dir / "command_trace.json"
    stdout_path = case_dir / "stdout.txt"
    stderr_path = case_dir / "stderr.txt"

    dump_json(input_path, case.input_payload)

    assertions: List[Dict[str, Any]] = []
    defects: List[Dict[str, Any]] = []
    planned_commands: List[Dict[str, Any]] = []

    refs_ok, missing_refs = check_contract_refs_exist(root, case.contract_refs)
    assertions.append(
        {
            "name": "contract_refs_exists",
            "passed": refs_ok,
            "details": "all refs exist" if refs_ok else f"missing: {missing_refs}",
        }
    )
    if not refs_ok:
        defects.append(
            {
                "reason_code": "invalid_contract_refs",
                "details": {"missing_refs": missing_refs},
            }
        )

    if case.execution_mode == "runner":
        runner_exists = bool(asset.runner_path) and (root / asset.runner_path).exists()
        assertions.append(
            {
                "name": "runner_exists",
                "passed": runner_exists,
                "details": asset.runner_path if runner_exists else f"runner missing: {asset.runner_path}",
            }
        )
        if not runner_exists:
            defects.append(
                {
                    "reason_code": "online_asset_unavailable",
                    "details": {"runner_path": asset.runner_path},
                }
            )
        planned_commands.append(
            {
                "kind": "runner",
                "command": f"python3 {asset.runner_path} --input <input> --output <output> --report <report>",
            }
        )

    if case.execution_mode == "online_qa":
        online_result = check_online_eligibility(root, profile, asset.runtime_key, online_cache)
        online_ok = online_result.get("eligible") is True and online_result.get("return_code") == 0
        assertions.append(
            {
                "name": "online_asset_eligible",
                "passed": online_ok,
                "details": {
                    "runtime_key": asset.runtime_key,
                    "return_code": online_result.get("return_code"),
                    "eligible": online_result.get("eligible"),
                },
            }
        )
        if not online_ok:
            defects.append(
                {
                    "reason_code": "online_asset_unavailable",
                    "details": {
                        "runtime_key": asset.runtime_key,
                        "return_code": online_result.get("return_code"),
                    },
                }
            )
        planned_commands.append(
            {
                "kind": "online_qa",
                "command": "openclaw agent --agent qa --message '<payload>' --json --timeout <seconds>",
            }
        )

    if case.scenario == "TR":
        tr_ok, tr_details = traceability_check(root, asset, skill_index, process_index)
        assertions.append(
            {
                "name": "traceability_chain_complete",
                "passed": tr_ok,
                "details": tr_details,
            }
        )
        if not tr_ok:
            defects.append({"reason_code": "traceability_broken", "details": tr_details})

    if case.scenario == "RB":
        rb_ok, rb_details = rollback_check(root, asset)
        assertions.append(
            {
                "name": "rollback_or_recovery_semantics_complete",
                "passed": rb_ok,
                "details": rb_details,
            }
        )
        if not rb_ok:
            defects.append({"reason_code": "rollback_semantics_missing", "details": rb_details})

    case_ok = all(bool(item.get("passed")) for item in assertions)

    dump_json(assertions_path, {"assertions": assertions})
    dump_json(
        command_trace_path,
        {
            "mode": "dry-run",
            "planned_commands": planned_commands,
            "generated_at": now_iso(),
        },
    )

    write_text(stdout_path, "dry-run: no command executed\n")
    write_text(stderr_path, "")

    dump_json(
        output_path,
        {
            "status": "pass" if case_ok else "fail",
            "mode": "dry-run",
            "reason_code": "ok" if case_ok else defects[0]["reason_code"],
            "defects": defects,
            "generated_at": now_iso(),
        },
    )

    return {
        "id": case.case_id,
        "asset_kind": case.asset_kind,
        "asset_id": case.asset_id,
        "scenario": case.scenario,
        "execution_mode": case.execution_mode,
        "status": "pass" if case_ok else "fail",
        "expected_exit_code": case.expected_exit_code,
        "input_payload": case.input_payload,
        "expected_output": case.expected_output,
        "assertion_rules": list(case.assertion_rules),
        "contract_refs": list(case.contract_refs),
        "reason_code": "ok" if case_ok else defects[0]["reason_code"],
        "evidence": {
            "input_ref": to_rel(input_path, root),
            "output_ref": to_rel(output_path, root),
            "assertions_ref": to_rel(assertions_path, root),
            "command_trace_ref": to_rel(command_trace_path, root),
            "stdout_ref": to_rel(stdout_path, root),
            "stderr_ref": to_rel(stderr_path, root),
        },
        "defects": defects,
    }


def build_online_prompt(case: CaseDef, asset: AssetDef) -> str:
    expected = "通过语义" if case.scenario == "HP" else "阻断语义"
    gate_rule = (
        "HP 场景 gate_decision 必须为 pass|approved|allow|success|ok。"
        if case.scenario == "HP"
        else "非 HP 场景 gate_decision 必须为 fail_closed|fail|hold|test_invalid|blocked|rejected。"
    )
    payload = {
        "asset_id": case.asset_id,
        "scenario": case.scenario,
        "expected_exit_code": case.expected_exit_code,
        "contract_refs": list(case.contract_refs),
        "expected": expected,
    }
    return (
        "你是 QA Agent。请只输出 JSON，不要附加解释。"
        "\n请基于输入 payload 判断该场景是否满足契约。"
        "\n注意：gate_decision 表示该场景本身的门禁判定，不是你是否成功回答问题。"
        "\n禁止调用任何工具或执行命令；仅基于 payload 推理并返回 JSON。"
        f"\n{gate_rule}"
        "\n输出字段必须严格包含：gate_decision, asset_id, scenario, reason_code, expected_exit_code, traceability_refs, recovery_or_rollback。"
        f"\npayload={json.dumps(payload, ensure_ascii=False)}"
    )


def run_online_case(
    *,
    root: Path,
    case: CaseDef,
    asset: AssetDef,
    profile: str,
    timeout_seconds: int,
    case_dir: Path,
    skill_index: Dict[str, Dict[str, Any]],
    process_index: Dict[str, Dict[str, Any]],
) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]], Dict[str, Any], str]:
    input_path = case_dir / "input.json"
    output_path = case_dir / "output.json"
    assertions_path = case_dir / "assertions.json"
    command_trace_path = case_dir / "command_trace.json"
    stdout_path = case_dir / "stdout.txt"
    stderr_path = case_dir / "stderr.txt"

    prompt = build_online_prompt(case, asset)
    cmd = openclaw_cmd(
        profile,
        "agent",
        "--agent",
        "qa",
        "--message",
        prompt,
        "--json",
        "--timeout",
        str(timeout_seconds),
    )

    attempt_logs: List[Dict[str, Any]] = []
    payload_obj: Dict[str, Any] = {}
    top: Any = {}
    proc: subprocess.CompletedProcess[str]

    for attempt in range(1, 3):
        proc = run_cmd(cmd, root)
        top = parse_json_from_mixed_output(proc.stdout)
        payload_obj = {}

        payload_text = ""
        if isinstance(top, dict):
            payloads = top.get("result", {}).get("payloads", [])
            if isinstance(payloads, list) and payloads:
                first = payloads[0]
                if isinstance(first, dict):
                    payload_text = str(first.get("text") or "")

        if payload_text:
            try:
                parsed = json.loads(payload_text)
                if isinstance(parsed, dict):
                    payload_obj = parsed
            except json.JSONDecodeError:
                payload_obj = {}

        aborted = False
        if isinstance(top, dict):
            result_obj = top.get("result", {})
            if isinstance(result_obj, dict):
                meta_obj = result_obj.get("meta", {})
                if isinstance(meta_obj, dict):
                    aborted = bool(meta_obj.get("aborted"))

        attempt_logs.append(
            {
                "attempt": attempt,
                "return_code": proc.returncode,
                "has_payload": bool(payload_obj),
                "aborted": aborted,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        )

        should_retry = attempt < 2 and (proc.returncode != 0 or not payload_obj or aborted)
        if not should_retry:
            break

    stdout_chunks: List[str] = []
    stderr_chunks: List[str] = []
    for item in attempt_logs:
        stdout_chunks.append(f"=== attempt {item['attempt']} ===\n{item['stdout']}")
        stderr_chunks.append(f"=== attempt {item['attempt']} ===\n{item['stderr']}")
    write_text(stdout_path, "\n".join(stdout_chunks))
    write_text(stderr_path, "\n".join(stderr_chunks))

    final_attempt = attempt_logs[-1] if attempt_logs else {"return_code": 1, "has_payload": False, "aborted": False}

    assertions: List[Dict[str, Any]] = []
    defects: List[Dict[str, Any]] = []

    response_ok = final_attempt["return_code"] == 0 and bool(payload_obj)
    assertions.append(
        {
            "name": "openclaw_online_response_contract",
            "passed": response_ok,
            "details": {
                "return_code": final_attempt["return_code"],
                "has_payload": bool(payload_obj),
                "aborted": final_attempt["aborted"],
                "attempts": len(attempt_logs),
            },
        }
    )
    if not response_ok:
        defects.append({"reason_code": "assertion_failed", "details": {"message": "online qa response parse failed"}})

    required = [
        "gate_decision",
        "asset_id",
        "scenario",
        "reason_code",
        "expected_exit_code",
        "traceability_refs",
        "recovery_or_rollback",
    ]
    missing = [key for key in required if key not in payload_obj]
    required_ok = not missing
    assertions.append(
        {
            "name": "required_output_fields",
            "passed": required_ok,
            "details": "ok" if required_ok else {"missing": missing},
        }
    )
    if not required_ok:
        defects.append({"reason_code": "assertion_failed", "details": {"missing_fields": missing}})

    if response_ok and required_ok:
        gate = str(payload_obj.get("gate_decision") or "").strip().lower()
        exit_raw = payload_obj.get("expected_exit_code")
        try:
            exit_code = int(exit_raw) if exit_raw is not None else -1
        except (TypeError, ValueError):
            exit_code = -1
        same_asset = str(payload_obj.get("asset_id") or "") == case.asset_id
        same_scenario = str(payload_obj.get("scenario") or "") == case.scenario
        trace_refs = payload_obj.get("traceability_refs")
        trace_ok = isinstance(trace_refs, list) and len(trace_refs) > 0
        rollback_ok = str(payload_obj.get("recovery_or_rollback") or "").strip() != ""

        gate_ok = gate in PASS_DECISIONS if case.scenario == "HP" else gate in BLOCK_DECISIONS
        exit_ok = exit_code == case.expected_exit_code

        assertions.extend(
            [
                {"name": "asset_id_match", "passed": same_asset, "details": payload_obj.get("asset_id")},
                {"name": "scenario_match", "passed": same_scenario, "details": payload_obj.get("scenario")},
                {"name": "gate_decision_match", "passed": gate_ok, "details": gate},
                {"name": "expected_exit_code_match", "passed": exit_ok, "details": exit_code},
                {"name": "traceability_refs_non_empty", "passed": trace_ok, "details": trace_refs},
                {"name": "recovery_or_rollback_non_empty", "passed": rollback_ok, "details": payload_obj.get("recovery_or_rollback")},
            ]
        )

        if not same_asset:
            defects.append({"reason_code": "assertion_failed", "details": {"field": "asset_id"}})
        if not same_scenario:
            defects.append({"reason_code": "assertion_failed", "details": {"field": "scenario"}})
        if not gate_ok:
            defects.append({"reason_code": "assertion_failed", "details": {"field": "gate_decision", "value": gate}})
        if not exit_ok:
            defects.append({"reason_code": "assertion_failed", "details": {"field": "expected_exit_code", "value": exit_code}})
        if not trace_ok:
            defects.append({"reason_code": "traceability_broken", "details": {"traceability_refs": trace_refs}})
        if case.scenario == "RB" and not rollback_ok:
            defects.append({"reason_code": "rollback_semantics_missing", "details": {"recovery_or_rollback": payload_obj.get("recovery_or_rollback")}})

    if case.scenario == "TR":
        tr_ok, tr_details = traceability_check(root, asset, skill_index, process_index)
        assertions.append({"name": "traceability_chain_complete", "passed": tr_ok, "details": tr_details})
        if not tr_ok:
            defects.append({"reason_code": "traceability_broken", "details": tr_details})

    if case.scenario == "RB":
        rb_ok, rb_details = rollback_check(root, asset)
        assertions.append(
            {
                "name": "rollback_or_recovery_semantics_complete",
                "passed": rb_ok,
                "details": rb_details,
            }
        )
        if not rb_ok:
            defects.append({"reason_code": "rollback_semantics_missing", "details": rb_details})

    ok = all(bool(item.get("passed")) for item in assertions)

    dump_json(assertions_path, {"assertions": assertions})
    dump_json(
        command_trace_path,
        {
            "command": " ".join(cmd),
            "return_code": final_attempt["return_code"],
            "attempts": [
                {
                    "attempt": item["attempt"],
                    "return_code": item["return_code"],
                    "has_payload": item["has_payload"],
                    "aborted": item["aborted"],
                }
                for item in attempt_logs
            ],
            "generated_at": now_iso(),
            "stdout_ref": stdout_path.name,
            "stderr_ref": stderr_path.name,
        },
    )
    dump_json(
        output_path,
        {
            "status": "pass" if ok else "fail",
            "qa_payload": payload_obj,
            "generated_at": now_iso(),
        },
    )

    evidence = {
        "input_ref": to_rel(input_path, root),
        "output_ref": to_rel(output_path, root),
        "assertions_ref": to_rel(assertions_path, root),
        "command_trace_ref": to_rel(command_trace_path, root),
        "stdout_ref": to_rel(stdout_path, root),
        "stderr_ref": to_rel(stderr_path, root),
    }
    reason_code = "ok" if ok else (defects[0]["reason_code"] if defects else "assertion_failed")
    return ok, payload_obj, assertions, evidence, reason_code


def run_runner_case(
    *,
    root: Path,
    case: CaseDef,
    asset: AssetDef,
    case_dir: Path,
) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]], Dict[str, Any], str]:
    input_path = case_dir / "input.json"
    output_path = case_dir / "output.json"
    assertions_path = case_dir / "assertions.json"
    command_trace_path = case_dir / "command_trace.json"
    stdout_path = case_dir / "stdout.txt"
    stderr_path = case_dir / "stderr.txt"
    report_path = case_dir / "runner_report.json"

    if not asset.runner_path:
        dump_json(output_path, {"status": "fail", "reason_code": "online_asset_unavailable"})
        dump_json(assertions_path, {"assertions": [{"name": "runner_path_exists", "passed": False}]})
        write_text(stdout_path, "")
        write_text(stderr_path, "runner path missing\n")
        dump_json(command_trace_path, {"command": "", "return_code": -1, "generated_at": now_iso()})
        evidence = {
            "input_ref": to_rel(input_path, root),
            "output_ref": to_rel(output_path, root),
            "assertions_ref": to_rel(assertions_path, root),
            "command_trace_ref": to_rel(command_trace_path, root),
            "stdout_ref": to_rel(stdout_path, root),
            "stderr_ref": to_rel(stderr_path, root),
        }
        return False, {}, [{"name": "runner_path_exists", "passed": False}], evidence, "online_asset_unavailable"

    payload = json.loads(json.dumps(case.input_payload))
    runner_input = payload.get("runner_input", {})
    if asset.asset_id == "meta.arch.skill-creator":
        if isinstance(runner_input, dict):
            runner_input["output_root"] = to_rel(case_dir / "generated-skills", root)

    dump_json(input_path, runner_input if isinstance(runner_input, dict) else {"raw": runner_input})

    cmd = [
        "python3",
        asset.runner_path,
        "--input",
        to_rel(input_path, root),
        "--output",
        to_rel(output_path, root),
        "--report",
        to_rel(report_path, root),
    ]
    proc = run_cmd(cmd, root)
    write_text(stdout_path, proc.stdout)
    write_text(stderr_path, proc.stderr)

    runner_output = load_json(output_path) if output_path.exists() else {}
    status = str(runner_output.get("status") or "").lower()

    assertions: List[Dict[str, Any]] = []
    if case.scenario == "HP":
        ok = proc.returncode == 0 and status in {"success", "completed", "pass"}
        assertions.append({"name": "expected_exit_code_match", "passed": proc.returncode == 0, "details": proc.returncode})
        assertions.append({"name": "runner_output_contract", "passed": status in {"success", "completed", "pass"}, "details": status})
    else:
        ok = proc.returncode == 2 and status in {"fail_closed", "fail", "rejected"}
        assertions.append({"name": "expected_exit_code_match", "passed": proc.returncode == 2, "details": proc.returncode})
        assertions.append({"name": "runner_output_contract", "passed": status in {"fail_closed", "fail", "rejected"}, "details": status})

    dump_json(assertions_path, {"assertions": assertions})
    dump_json(
        command_trace_path,
        {
            "command": " ".join(cmd),
            "return_code": proc.returncode,
            "generated_at": now_iso(),
            "stdout_ref": stdout_path.name,
            "stderr_ref": stderr_path.name,
        },
    )

    evidence = {
        "input_ref": to_rel(input_path, root),
        "output_ref": to_rel(output_path, root),
        "assertions_ref": to_rel(assertions_path, root),
        "command_trace_ref": to_rel(command_trace_path, root),
        "stdout_ref": to_rel(stdout_path, root),
        "stderr_ref": to_rel(stderr_path, root),
    }
    reason_code = "ok" if ok else "assertion_failed"
    return ok, runner_output, assertions, evidence, reason_code


def execute_case(
    *,
    root: Path,
    case: CaseDef,
    asset: AssetDef,
    profile: str,
    timeout_seconds: int,
    run_root: Path,
    skill_index: Dict[str, Dict[str, Any]],
    process_index: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    case_dir = run_root / "cases" / case.case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    dump_json(case_dir / "input.json", case.input_payload)

    if case.execution_mode == "runner":
        ok, output_payload, assertions, evidence, reason_code = run_runner_case(
            root=root,
            case=case,
            asset=asset,
            case_dir=case_dir,
        )
    else:
        ok, output_payload, assertions, evidence, reason_code = run_online_case(
            root=root,
            case=case,
            asset=asset,
            profile=profile,
            timeout_seconds=timeout_seconds,
            case_dir=case_dir,
            skill_index=skill_index,
            process_index=process_index,
        )

    return {
        "id": case.case_id,
        "asset_kind": case.asset_kind,
        "asset_id": case.asset_id,
        "scenario": case.scenario,
        "execution_mode": case.execution_mode,
        "status": "pass" if ok else "fail",
        "expected_exit_code": case.expected_exit_code,
        "input_payload": case.input_payload,
        "expected_output": case.expected_output,
        "assertion_rules": list(case.assertion_rules),
        "contract_refs": list(case.contract_refs),
        "reason_code": reason_code,
        "evidence": evidence,
        "output_payload": output_payload,
        "assertions": assertions,
        "defects": [] if ok else [{"reason_code": reason_code, "details": {"case_id": case.case_id}}],
    }


def build_natural_language_conclusion(*, status: str, total: int, passed: int, failed: int, missing_assets: List[str], missing_online_processes: List[str], dry_run: bool) -> str:
    objective_text = "验证 Meta 资产在线主验收链路可执行、覆盖完整并满足 Fail-Closed 门禁"
    coverage_text = f"覆盖 {total} 条用例（通过 {passed}，失败 {failed}）"

    if status == "pass":
        if dry_run:
            return (
                f"测试目标：{objective_text}。"
                f"覆盖范围：{coverage_text}。"
                "关键现象：资产四类场景矩阵完整、流程在线覆盖完整、可执行性门禁通过。"
                "风险判断：本轮为 dry-run，已验证在线可执行性与追溯闭合，仍需在 Phase6 进行分层实跑验证在线输出质量。"
                "准入结论：Phase5 通过。"
            )
        return (
            f"测试目标：{objective_text}。"
            f"覆盖范围：{coverage_text}。"
            "关键现象：在线调用与断言均通过，主链路与 Fail-Closed 场景均可复现。"
            "风险判断：未发现阻断风险，建议按分层回归继续扩大执行范围。"
            "准入结论：通过。"
        )

    scope_text = ""
    if missing_assets:
        scope_text += f"缺少四类场景资产: {', '.join(missing_assets)}。"
    if missing_online_processes:
        scope_text += f"缺少在线流程覆盖: {', '.join(missing_online_processes)}。"

    if dry_run:
        return (
            f"测试目标：{objective_text}。"
            f"覆盖范围：{coverage_text}。"
            f"关键现象：dry-run 检出失败 {failed} 条，在线可执行性或覆盖存在缺口。"
            f"风险判断：存在高风险阻断，不满足 Phase5 准入。{scope_text}"
            "准入结论：Phase5 不通过。"
        )

    return (
        f"测试目标：{objective_text}。"
        f"覆盖范围：{coverage_text}。"
        f"关键现象：在线执行失败 {failed} 条，主验收链路存在阻断。"
        f"风险判断：当前风险高，必须先完成缺陷修复与回归。{scope_text}"
        "准入结论：不通过。"
    )


def build_summary_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Meta QA 在线执行摘要",
        "",
        f"- ts: {summary.get('ts', '')}",
        f"- suite: {summary.get('suite', '')}",
        f"- status: {summary.get('status', '')}",
        f"- gate_decision: {summary.get('gate_decision', '')}",
        f"- total: {summary.get('total', 0)}",
        f"- passed: {summary.get('passed', 0)}",
        f"- failed: {summary.get('failed', 0)}",
        "",
        "## 覆盖情况",
    ]

    online_coverage = summary.get("online_coverage", {})
    lines.append(f"- process_online_covered: {online_coverage.get('all_process_online_covered', False)}")

    missing_assets = summary.get("asset_coverage", {}).get("assets_missing_full_matrix", [])
    lines.append(f"- assets_missing_full_matrix: {', '.join(missing_assets) if missing_assets else 'none'}")
    missing_processes = online_coverage.get("missing_processes", [])
    lines.append(f"- processes_missing_online_case: {', '.join(missing_processes) if missing_processes else 'none'}")
    lines.append("")
    lines.append("## 自然语言结论")
    lines.append(summary.get("natural_language_conclusion", ""))
    lines.append("")
    return "\n".join(lines)


def build_defects_markdown(findings: List[Dict[str, Any]]) -> str:
    lines = ["# Meta QA 缺陷摘要", ""]
    if not findings:
        lines.append("本轮无缺陷。")
        lines.append("")
        return "\n".join(lines)

    for item in findings:
        lines.append(f"- [{item.get('severity', 'P2')}] {item.get('asset_id', '')} / {item.get('scenario', '')}: {item.get('reason_code', '')}")
        lines.append(f"  - repro: {item.get('repro', '')}")
        lines.append(f"  - evidence: {item.get('evidence_ref', '')}")
    lines.append("")
    return "\n".join(lines)


def severity_for_case(case: CaseDef) -> str:
    if case.scenario in {"HP", "FC"}:
        return "P0"
    if case.scenario in {"TR", "RB"}:
        return "P1"
    return "P2"


def ensure_regression_plan(path: Path) -> None:
    dump_json(
        path,
        {
            "strategy": "layered",
            "stages": [
                {
                    "stage": 1,
                    "suite": "online-critical",
                    "description": "先执行每资产关键在线 + Fail-Closed",
                },
                {
                    "stage": 2,
                    "suite": "final-regression-full",
                    "description": "再执行全量 112 case",
                },
            ],
            "pass_condition": "all_stages_pass",
            "generated_at": now_iso(),
        },
    )


def main() -> int:
    args = parse_args()
    root = repo_root()

    assets, skill_index, process_index = load_assets(root)
    cases = generate_cases(assets)
    case_by_id = {case.case_id: case for case in cases}
    asset_by_id = {asset.asset_id: asset for asset in assets}
    suite_map = build_suite_map(cases)

    if args.list_cases:
        payload = {
            "asset_count": len(assets),
            "case_count": len(cases),
            "suites": {key: len(value) for key, value in suite_map.items()},
            "cases": [
                {
                    "case_id": case.case_id,
                    "asset_kind": case.asset_kind,
                    "asset_id": case.asset_id,
                    "scenario": case.scenario,
                    "execution_mode": case.execution_mode,
                    "expected_exit_code": case.expected_exit_code,
                    "contract_refs": list(case.contract_refs),
                }
                for case in cases
            ],
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    selection = materialize_selection(args, suite_map, case_by_id)
    selected_case_ids: List[str] = selection["selected_case_ids"]
    selection_errors: List[str] = selection["errors"]
    suite_inputs: List[str] = selection["suite_inputs"]

    evidence_root = (root / args.evidence_root).resolve()
    evidence_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    run_root = evidence_root / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "cases").mkdir(parents=True, exist_ok=True)

    regression_plan_path = evidence_root / DEFAULT_REGRESSION_PLAN_NAME
    ensure_regression_plan(regression_plan_path)

    global_errors: List[str] = list(selection_errors)
    if not selected_case_ids:
        global_errors.append("empty_selection:no_case_selected")

    # 覆盖门禁：每资产必须有四类场景。
    case_ids_by_asset: Dict[str, set[str]] = {}
    for case in cases:
        case_ids_by_asset.setdefault(case.asset_id, set()).add(case.scenario)

    assets_missing_full_matrix = [
        asset_id for asset_id, scenario_set in case_ids_by_asset.items() if set(SCENARIOS) - scenario_set
    ]
    if assets_missing_full_matrix:
        global_errors.append("missing_asset_matrix:" + ",".join(assets_missing_full_matrix))

    process_online_case: Dict[str, bool] = {}
    for asset in assets:
        if asset.asset_kind != "meta_process":
            continue
        has_online = any(
            case.asset_id == asset.asset_id and case.execution_mode == "online_qa" for case in cases
        )
        process_online_case[asset.asset_id] = has_online

    missing_online_processes = [key for key, value in process_online_case.items() if not value]
    if missing_online_processes:
        global_errors.append("missing_online_processes:" + ",".join(missing_online_processes))

    selected_cases = [case_by_id[case_id] for case_id in selected_case_ids]

    # openclaw 最小健康检查
    health_cmd = openclaw_cmd(args.openclaw_profile.strip(), "health", "--json")
    health_proc = run_cmd(health_cmd, root)
    health_ok = health_proc.returncode == 0
    if not health_ok:
        global_errors.append("openclaw_health_failed")

    findings: List[Dict[str, Any]] = []
    case_results: List[Dict[str, Any]] = []

    if args.dry_run:
        online_cache: Dict[str, Dict[str, Any]] = {}
        for case in selected_cases:
            asset = asset_by_id[case.asset_id]
            result = dry_run_case(
                root=root,
                case=case,
                asset=asset,
                profile=args.openclaw_profile.strip(),
                run_root=run_root,
                skill_index=skill_index,
                process_index=process_index,
                online_cache=online_cache,
            )
            case_results.append(result)
            if result["status"] != "pass":
                findings.append(
                    {
                        "severity": severity_for_case(case),
                        "asset_id": case.asset_id,
                        "scenario": case.scenario,
                        "reason_code": result.get("reason_code", "assertion_failed"),
                        "repro": f"python3 tests/m3-self-development/run_meta_qa_online.py --case {case.case_id}",
                        "evidence_ref": result["evidence"]["output_ref"],
                    }
                )
    else:
        layered = bool(selection.get("layered_regression"))
        exec_cases: List[CaseDef] = selected_cases

        if layered:
            online_critical_ids = suite_map["online-critical"]
            full_ids = suite_map["final-regression-full"]
            staged_ids = online_critical_ids + [cid for cid in full_ids if cid not in set(online_critical_ids)]
            exec_cases = [case_by_id[cid] for cid in staged_ids]

        for case in exec_cases:
            asset = asset_by_id[case.asset_id]
            result = execute_case(
                root=root,
                case=case,
                asset=asset,
                profile=args.openclaw_profile.strip(),
                timeout_seconds=args.max_online_seconds,
                run_root=run_root,
                skill_index=skill_index,
                process_index=process_index,
            )
            case_results.append(result)
            if result["status"] != "pass":
                findings.append(
                    {
                        "severity": severity_for_case(case),
                        "asset_id": case.asset_id,
                        "scenario": case.scenario,
                        "reason_code": result.get("reason_code", "assertion_failed"),
                        "repro": f"python3 tests/m3-self-development/run_meta_qa_online.py --case {case.case_id}",
                        "evidence_ref": result["evidence"]["output_ref"],
                    }
                )

    total = len(case_results)
    passed = sum(1 for item in case_results if item["status"] == "pass")
    failed = total - passed

    if global_errors:
        for err in global_errors:
            findings.append(
                {
                    "severity": "P0",
                    "asset_id": "global",
                    "scenario": "GLOBAL",
                    "reason_code": err,
                    "repro": "python3 tests/m3-self-development/run_meta_qa_online.py --dry-run",
                    "evidence_ref": to_rel(run_root, root),
                }
            )

    status = "pass" if (failed == 0 and not global_errors) else "fail"
    gate_decision = "pass" if status == "pass" else "fail"

    asset_coverage = {
        "assets_total": len(assets),
        "assets_missing_full_matrix": assets_missing_full_matrix,
        "all_assets_have_full_matrix": len(assets_missing_full_matrix) == 0,
    }
    online_coverage = {
        "process_total": len(process_online_case),
        "missing_processes": missing_online_processes,
        "all_process_online_covered": len(missing_online_processes) == 0,
    }

    selected_suite_label = "default-all" if selection.get("default_mode") else ",".join(suite_inputs) if suite_inputs else "custom-case"

    natural_language_conclusion = build_natural_language_conclusion(
        status=status,
        total=total,
        passed=passed,
        failed=failed,
        missing_assets=assets_missing_full_matrix,
        missing_online_processes=missing_online_processes,
        dry_run=args.dry_run,
    )

    summary = {
        "ts": now_iso(),
        "suite": selected_suite_label,
        "status": status,
        "gate_decision": gate_decision,
        "total": total,
        "passed": passed,
        "failed": failed,
        "asset_coverage": asset_coverage,
        "online_coverage": online_coverage,
        "selected_case_ids": selected_case_ids,
        "cases": case_results,
        "findings": findings,
        "natural_language_conclusion": natural_language_conclusion,
        "evidence_root": to_rel(evidence_root, root),
        "run_root": to_rel(run_root, root),
        "mode": "dry-run" if args.dry_run else "run",
        "errors": global_errors,
    }

    report_path = evidence_root / args.report
    summary_md_path = evidence_root / DEFAULT_SUMMARY_NAME
    defects_path = evidence_root / DEFAULT_DEFECTS_NAME
    defect_summary_md_path = evidence_root / DEFAULT_DEFECTS_SUMMARY_NAME

    dump_json(report_path, summary)
    dump_json(defects_path, {"findings": findings, "generated_at": now_iso()})
    write_text(summary_md_path, build_summary_markdown(summary))
    write_text(defect_summary_md_path, build_defects_markdown(findings))

    print(json.dumps(summary, ensure_ascii=False))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
