#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


CASE_HEADER_RE = re.compile(r"^###\s+(TC-\d+)(?::\s*(.*))?$")
TOP_BULLET_RE = re.compile(r"^-\s+([^:]+):\s*(.*)$")
NESTED_BULLET_RE = re.compile(r"^\s+-\s+(.*)$")


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"missing_file:{path}")
    return path.read_text(encoding="utf-8")


def normalize_key(raw: str) -> str:
    return raw.strip().lower().replace(" ", "_").replace("-", "_")


def parse_bracket_list(raw: str) -> List[str]:
    text = raw.strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    parts = [p.strip().strip("'\"") for p in text.split(",")]
    return [p for p in parts if p]


def parse_section_bullets(lines: List[str]) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        match = TOP_BULLET_RE.match(line.strip())
        if not match:
            i += 1
            continue
        key = normalize_key(match.group(1))
        value = match.group(2).strip()

        nested_items: List[str] = []
        j = i + 1
        while j < len(lines):
            nested_line = lines[j]
            if TOP_BULLET_RE.match(nested_line.strip()):
                break
            nested_match = NESTED_BULLET_RE.match(nested_line)
            if nested_match:
                nested_items.append(nested_match.group(1).strip())
            j += 1

        if nested_items:
            as_dict: Dict[str, Any] = {}
            as_list: List[str] = []
            for item in nested_items:
                if ":" in item:
                    sub_key, sub_value = item.split(":", 1)
                    sub_key = normalize_key(sub_key)
                    sub_value = sub_value.strip()
                    if sub_key == "expected_conditions":
                        as_dict[sub_key] = parse_bracket_list(sub_value) if sub_value else []
                    else:
                        as_dict[sub_key] = sub_value
                else:
                    as_list.append(item)
            if as_dict and not as_list:
                parsed[key] = as_dict
            elif as_dict and as_list:
                parsed[key] = {"items": as_list, "fields": as_dict}
            else:
                parsed[key] = as_list
        else:
            if key in {"judge_perspectives"}:
                parsed[key] = parse_bracket_list(value)
            else:
                parsed[key] = value

        i = j
    return parsed


def split_test_doc(text: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    lines = text.splitlines()
    cases: List[Dict[str, Any]] = []
    case_buffer: List[str] = []
    current_case: Optional[Dict[str, Any]] = None
    in_eval_cfg = False
    eval_cfg_lines: List[str] = []

    for line in lines:
        case_header_match = CASE_HEADER_RE.match(line.strip())
        if line.strip().startswith("## Evaluation Configuration"):
            in_eval_cfg = True
            if current_case is not None:
                current_case.update(parse_section_bullets(case_buffer))
                cases.append(current_case)
                current_case = None
                case_buffer = []
            continue

        if case_header_match and not in_eval_cfg:
            if current_case is not None:
                current_case.update(parse_section_bullets(case_buffer))
                cases.append(current_case)
            current_case = {
                "tc_id": case_header_match.group(1),
                "title": (case_header_match.group(2) or "").strip(),
            }
            case_buffer = []
            continue

        if in_eval_cfg:
            eval_cfg_lines.append(line)
        elif current_case is not None:
            case_buffer.append(line)

    if current_case is not None:
        current_case.update(parse_section_bullets(case_buffer))
        cases.append(current_case)

    eval_cfg = parse_section_bullets(eval_cfg_lines)
    return cases, eval_cfg


def ensure_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        return parse_bracket_list(text)
    return [text]


def parse_json_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    text = str(value).strip()
    if not text:
        return {}
    if text.startswith("{") and text.endswith("}"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}
    return {}


def to_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    if value is None:
        return default
    nums = re.findall(r"\d+", str(value))
    if not nums:
        return default
    return int(nums[0])


def build_datapoints(
    raw_cases: List[Dict[str, Any]],
    objective_ref: str,
    spec_ref: str,
    profile_ids: List[str],
    test_doc_ref: str,
    eval_cfg: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, str], List[str], List[str]]:
    datapoints: List[Dict[str, Any]] = []
    tc_profile_map: Dict[str, str] = {}
    warnings: List[str] = []
    contract_errors: List[str] = []

    if not profile_ids:
        contract_errors.append("empty_profile_set")
        return [], {}, warnings, contract_errors

    baseline = profile_ids[0]
    default_grader_selection = (
        eval_cfg.get("grader_selection")
        or eval_cfg.get("default_grader_selection")
        or []
    )
    default_grader_weights = (
        eval_cfg.get("grader_weights")
        or eval_cfg.get("default_grader_weights")
        or {}
    )
    default_min_score_per_grader = (
        eval_cfg.get("min_score_per_grader")
        or eval_cfg.get("default_min_score_per_grader")
        or {}
    )
    default_must_pass_graders = (
        eval_cfg.get("must_pass_graders")
        or eval_cfg.get("default_must_pass_graders")
        or []
    )

    for index, case in enumerate(raw_cases, start=1):
        tc_id = case.get("tc_id", "").strip()
        if not tc_id:
            contract_errors.append(f"case_{index}_missing_tc_id")
            continue

        priority = str(case.get("priority", "")).strip()
        eval_method = str(case.get("evaluation_method", "")).strip()
        if not priority:
            contract_errors.append(f"{tc_id}:missing_priority")
        if not eval_method:
            contract_errors.append(f"{tc_id}:missing_evaluation_method")

        judge_payload = case.get("judge_payload", {})
        if not isinstance(judge_payload, dict):
            judge_payload = {}
        # Some TEST.md files flatten judge payload fields at case level.
        for key in [
            "objective",
            "spec_ref",
            "expected_conditions",
            "actual_output_ref",
            "baseline_output_ref",
            "candidate_output_ref",
            "reference_response",
            "context",
            "grader_selection",
            "grader_weights",
            "min_score_per_grader",
            "must_pass_graders",
            "grader_plan",
            "subjective_rounds",
            "seed",
            "judge_model",
            "judge_base_url",
        ]:
            if key in case and key not in judge_payload:
                judge_payload[key] = case[key]
        expected = case.get("expected")
        expected_conditions = (
            ensure_list(judge_payload.get("expected_conditions"))
            or ensure_list(case.get("expected_conditions"))
            or ensure_list(expected)
        )

        if eval_method.lower() == "llm-judge" and not expected_conditions:
            contract_errors.append(f"{tc_id}:llm_judge_missing_expected_conditions")

        if not expected_conditions:
            warnings.append(f"{tc_id}:missing_expected_conditions")

        case_grader_selection = case.get("grader_selection") or default_grader_selection
        case_grader_weights = case.get("grader_weights") or default_grader_weights
        case_min_score_per_grader = case.get("min_score_per_grader") or default_min_score_per_grader
        case_must_pass_graders = case.get("must_pass_graders") or default_must_pass_graders

        profile_id = baseline
        tc_profile_map[tc_id] = profile_id

        datapoints.append(
            {
                "tc_id": tc_id,
                "title": case.get("title", ""),
                "index": index,
                "type": case.get("type", "Objective"),
                "priority": priority,
                "evaluation_method": eval_method or "Rule Match",
                "input_payload": case.get("input"),
                "expected": expected,
                "expected_conditions": expected_conditions,
                "judge_payload": judge_payload,
                "grader_plan": case.get("grader_plan"),
                "grader_selection": case_grader_selection,
                "grader_weights": case_grader_weights,
                "min_score_per_grader": case_min_score_per_grader,
                "must_pass_graders": case_must_pass_graders,
                "objective_ref": objective_ref,
                "spec_ref": spec_ref,
                "profile_id": profile_id,
                "test_doc_ref": test_doc_ref,
            }
        )

    return datapoints, tc_profile_map, warnings, contract_errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile TEST.md into structured datapoints")
    parser.add_argument("--test-doc", required=True)
    parser.add_argument("--objective-ref", required=True)
    parser.add_argument("--spec-ref", required=True)
    parser.add_argument("--profile-set", required=True, help="Comma-separated profile ids")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "compile_report.json"
    datapoints_path = output_dir / "test_datapoints.json"
    mapping_path = output_dir / "tc_profile_map.json"
    now = dt.datetime.now(dt.timezone.utc).isoformat()

    payload = {
        "test_datapoints_ref": str(datapoints_path),
        "tc_profile_map_ref": str(mapping_path),
        "compile_report_ref": str(report_path),
        "gate_decision": "fail",
        "evidence_ref": str(output_dir),
        "reasons": [],
    }

    try:
        test_doc = Path(args.test_doc)
        text = load_text(test_doc)
        raw_cases, eval_cfg = split_test_doc(text)
        profiles = [item.strip() for item in args.profile_set.split(",") if item.strip()]

        if not raw_cases:
            payload["gate_decision"] = "test_invalid"
            payload["reasons"] = ["no_tc_cases"]
            report_path.write_text(
                json.dumps({"status": "parse_error", "reason": "no_tc_cases", "timestamp": now}, indent=2),
                encoding="utf-8",
            )
            print(json.dumps(payload, ensure_ascii=True))
            return 20

        datapoints, tc_profile_map, warnings, contract_errors = build_datapoints(
            raw_cases=raw_cases,
            objective_ref=args.objective_ref,
            spec_ref=args.spec_ref,
            profile_ids=profiles,
            test_doc_ref=str(test_doc),
            eval_cfg=eval_cfg,
        )

        has_p0 = any(str(case.get("priority", "")).strip() == "P0" for case in raw_cases)
        if contract_errors:
            payload["gate_decision"] = "test_invalid"
            payload["reasons"] = ["invalid_test_contract"] + contract_errors
            report_path.write_text(
                json.dumps(
                    {
                        "status": "test_invalid",
                        "contract_errors": contract_errors,
                        "warnings": warnings,
                        "timestamp": now,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(json.dumps(payload, ensure_ascii=True))
            return 20

        if not has_p0:
            payload["gate_decision"] = "fail"
            payload["reasons"] = ["missing_p0_case"]
            report_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "reason": "missing_p0_case",
                        "warnings": warnings,
                        "timestamp": now,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(json.dumps(payload, ensure_ascii=True))
            return 40

        if len(datapoints) != len(tc_profile_map):
            payload["gate_decision"] = "fail"
            payload["reasons"] = ["tc_profile_mapping_mismatch"]
            report_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "reason": "tc_profile_mapping_mismatch",
                        "datapoints": len(datapoints),
                        "mapping": len(tc_profile_map),
                        "timestamp": now,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(json.dumps(payload, ensure_ascii=True))
            return 40

        compile_meta = {
            "compiled_at": now,
            "test_doc_ref": str(test_doc),
            "objective_ref": args.objective_ref,
            "spec_ref": args.spec_ref,
            "profile_set": profiles,
            "evaluation_configuration": {
                "objective_eval_rounds": to_int(eval_cfg.get("objective_eval_rounds"), default=1),
                "subjective_eval_rounds": to_int(eval_cfg.get("subjective_eval_rounds"), default=0),
                "subjective_seed": to_int(eval_cfg.get("seed"), default=42),
                "judge_perspectives": ensure_list(eval_cfg.get("judge_perspectives")),
                "timeout_seconds": to_int(eval_cfg.get("timeout_seconds"), default=600),
                "retry_policy": str(eval_cfg.get("retry_policy", "")).strip(),
                "grader_selection": ensure_list(
                    eval_cfg.get("grader_selection")
                    or eval_cfg.get("default_grader_selection")
                ),
                "grader_weights": parse_json_dict(
                    eval_cfg.get("grader_weights")
                    or eval_cfg.get("default_grader_weights")
                ),
                "min_score_per_grader": parse_json_dict(
                    eval_cfg.get("min_score_per_grader")
                    or eval_cfg.get("default_min_score_per_grader")
                ),
                "must_pass_graders": ensure_list(
                    eval_cfg.get("must_pass_graders")
                    or eval_cfg.get("default_must_pass_graders")
                ),
            },
            "case_count": len(datapoints),
            "p0_case_count": sum(1 for case in raw_cases if str(case.get("priority", "")).strip() == "P0"),
            "warnings": warnings,
        }

        datapoints_path.write_text(json.dumps({"datapoints": datapoints, "metadata": compile_meta}, indent=2), encoding="utf-8")
        mapping_path.write_text(
            json.dumps(
                {
                    "profile_ids": profiles,
                    "tc_profile_map": tc_profile_map,
                    "default_profile_id": profiles[0],
                    "compiled_at": now,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        report_path.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "gate_decision": "pass",
                    "reasons": ["compile_success"],
                    "compile_meta": compile_meta,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        payload["gate_decision"] = "pass"
        payload["reasons"] = ["compile_success"]
        print(json.dumps(payload, ensure_ascii=True))
        return 0
    except Exception as exc:
        report_path.write_text(
            json.dumps({"status": "fail", "error": str(exc), "timestamp": now}, indent=2),
            encoding="utf-8",
        )
        payload["gate_decision"] = "fail"
        payload["reasons"] = ["exception", str(exc)]
        print(json.dumps(payload, ensure_ascii=True))
        return 40


if __name__ == "__main__":
    raise SystemExit(main())
