import importlib.util
import sys
from pathlib import Path


def load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_registry_tool_falls_back_to_round_dir_filename() -> None:
    worktree_root = Path(__file__).resolve().parents[1]
    parent_repo_root = worktree_root.parents[1]
    tool = load_module(worktree_root / "shared/registry/registry_contract_tool.py", "registry_contract_tool")

    round_dir = (
        parent_repo_root
        / "runtime_data/execution/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01"
    ).resolve()
    evidence_ref = "runtime_data/execution/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/round-evidence.jsonl"

    resolved = tool._resolve_artifact_path(round_dir, evidence_ref)

    assert resolved == (round_dir / "round-evidence.jsonl").resolve()
    assert resolved.exists()


def test_run_tc_online_uses_absolute_path_for_external_artifact() -> None:
    worktree_root = Path(__file__).resolve().parents[1]
    tc_module = load_module(
        worktree_root / "tests/m3-self-development/run_tc_online.py",
        "run_tc_online_path_arg",
    )

    external_path = (
        worktree_root.parents[1]
        / "tmp/runtime_data/execution/evidence/construction-plane/"
        "R-20260222-M6-m3-self-development-e2e-online-01/session5/session5_report.json"
    ).resolve()

    rendered = tc_module.path_arg_for_root(external_path, worktree_root)

    assert rendered == str(external_path)


def test_semantic_validation_eval_cmd_enforces_strict_llm_threshold() -> None:
    worktree_root = Path(__file__).resolve().parents[1]
    semantic_module = load_module(
        worktree_root / "tests/m1-runtime/run_semantic_service_validation.py",
        "run_semantic_service_validation_cmd",
    )

    cmd = semantic_module.build_semantic_eval_cmd(
        preparation_bundle_ref="tmp/preparation_bundle.index.json",
        actual_output_ref="tmp/mock_delivery_output.md",
        judge_model="gpt-5.3-codex",
        output_dir_ref="tmp/evaluation",
        llm_threshold=4.0,
    )

    assert "--llm-threshold" in cmd
    idx = cmd.index("--llm-threshold")
    assert cmd[idx + 1] == "4.0"

