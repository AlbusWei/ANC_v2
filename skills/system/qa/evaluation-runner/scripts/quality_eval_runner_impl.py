#!/usr/bin/env python3
import argparse
import asyncio
import datetime as dt
import json
import os
import random
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openjudge.graders.common.correctness import CorrectnessGrader
from openjudge.graders.common.hallucination import HallucinationGrader
from openjudge.graders.common.harmfulness import HarmfulnessGrader
from openjudge.graders.common.instruction_following import InstructionFollowingGrader
from openjudge.graders.common.relevance import RelevanceGrader
from openjudge.graders.format.json.json_match import JsonMatchGrader
from openjudge.graders.format.json.json_validator import JsonValidatorGrader
from openjudge.graders.llm_grader import LLMGrader
from openjudge.graders.schema import GraderMode
from openjudge.graders.text.similarity import SimilarityGrader
from openjudge.graders.text.string_match import StringMatchGrader
from openjudge.generator.simple_rubric import (
    SimpleRubricsGenerator,
    SimpleRubricsGeneratorConfig,
)
from openjudge.models.openai_chat_model import OpenAIChatModel
from openjudge.runner.grading_runner import GradingRunner


VALID_MODES = {"objective", "subjective", "regression"}
VALID_DECISIONS = {"pass", "fail", "hold", "test_invalid"}
LLM_SCORE_GRADERS = {
    "relevance",
    "correctness",
    "hallucination",
    "instruction_following",
    "harmfulness",
    "auto_rubric",
}
SUPPORTED_GRADERS = {
    "relevance",
    "correctness",
    "hallucination",
    "instruction_following",
    "harmfulness",
    "json_validator",
    "json_match",
    "string_match",
    "similarity",
    "auto_rubric",
}
GRADER_ALIASES = {
    "instruction": "instruction_following",
    "instruction-following": "instruction_following",
    "instruction_following": "instruction_following",
    "json": "json_validator",
    "json-format": "json_validator",
    "json_validator": "json_validator",
    "json-match": "json_match",
    "json_match": "json_match",
    "match": "string_match",
    "string-match": "string_match",
    "string_match": "string_match",
    "text-similarity": "similarity",
    "text_similarity": "similarity",
}
JUDGE_ERROR_MODEL_UNSUPPORTED_MARKERS = [
    "model is not supported",
    "unsupported model",
    "unsupported_model",
    "model_not_found",
    "model does not exist",
    "invalid model",
    "not supported when using codex with a chatgpt account",
]
JUDGE_ERROR_AUTH_MARKERS = [
    "invalid_api_key",
    "invalid api key",
    "unauthorized",
    "authentication",
    "permission denied",
    "forbidden",
    "401",
]
JUDGE_ERROR_INVALID_REQUEST_MARKERS = [
    "invalid_request_error",
    "bad request",
    "error code: 400",
    "invalid parameter",
]


class ContractError(Exception):
    pass


class TransientJudgeError(Exception):
    pass


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def code_for(decision: str) -> int:
    if decision == "pass":
        return 0
    if decision == "test_invalid":
        return 20
    if decision == "hold":
        return 30
    if decision == "fail":
        return 40
    return 50


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def load_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        raise ContractError("missing_%s:%s" % (label, path))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError("invalid_json_%s:%s" % (label, exc)) from exc


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join([normalize_text(item) for item in value])
    if isinstance(value, dict):
        for key in ("response", "output", "content", "text", "actual_output"):
            if key in value:
                return normalize_text(value[key])
    return json.dumps(value, ensure_ascii=True)


def load_output_ref(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ContractError("missing_actual_output_ref:%s" % path)
    raw_text = path.read_text(encoding="utf-8")
    parsed_json: Optional[Any] = None
    if path.suffix.lower() == ".json":
        try:
            parsed_json = json.loads(raw_text)
        except json.JSONDecodeError:
            parsed_json = None
    return {
        "ref": str(path),
        "text": normalize_text(parsed_json if parsed_json is not None else raw_text),
        "raw": parsed_json if parsed_json is not None else raw_text,
    }


def clean_ref(raw: str) -> str:
    text = str(raw).strip()
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        text = text[1:-1]
    return text.strip().strip("'\"")


def parse_preparation_bundle(bundle_path: Path) -> Dict[str, Any]:
    bundle = load_json(bundle_path, "preparation_bundle")
    required_fields = {
        "objective_ref",
        "spec_ref",
        "test_doc_ref",
        "test_datapoints_ref",
        "tc_profile_map_ref",
        "compile_report_ref",
        "producer_process_id",
        "timestamps",
    }
    missing = sorted([field for field in required_fields if field not in bundle])
    if missing:
        raise ContractError("bundle_missing_fields:%s" % ",".join(missing))

    compile_report_path = Path(str(bundle["compile_report_ref"]))
    compile_report = load_json(compile_report_path, "compile_report")
    compile_status = str(compile_report.get("status", "")).lower()
    if compile_status in {"test_invalid", "parse_error"}:
        raise ContractError("compile_report_invalid")

    datapoints_payload = load_json(Path(str(bundle["test_datapoints_ref"])), "test_datapoints")
    if "datapoints" in datapoints_payload:
        datapoints = datapoints_payload.get("datapoints", [])
        compile_meta = datapoints_payload.get("metadata", {})
    elif isinstance(datapoints_payload, list):
        datapoints = datapoints_payload
        compile_meta = {}
    else:
        raise ContractError("invalid_test_datapoints_payload")

    if not datapoints:
        raise ContractError("empty_test_datapoints")

    profile_payload = load_json(Path(str(bundle["tc_profile_map_ref"])), "tc_profile_map")
    if "tc_profile_map" in profile_payload:
        tc_profile_map = profile_payload.get("tc_profile_map", {})
        profile_ids = profile_payload.get("profile_ids", [])
    else:
        tc_profile_map = profile_payload
        profile_ids = []

    if not isinstance(tc_profile_map, dict) or not tc_profile_map:
        raise ContractError("invalid_tc_profile_map")

    return {
        "bundle": bundle,
        "compile_report": compile_report,
        "datapoints": datapoints,
        "compile_meta": compile_meta,
        "tc_profile_map": tc_profile_map,
        "profile_ids": profile_ids,
    }


def resolve_case_output(
    case: Dict[str, Any],
    case_index: int,
    all_cases: List[Dict[str, Any]],
    actual_outputs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    judge_payload = case.get("judge_payload", {})
    if isinstance(judge_payload, dict):
        explicit_ref = clean_ref(judge_payload.get("actual_output_ref", ""))
        if explicit_ref:
            return load_output_ref(Path(explicit_ref))

    if len(actual_outputs) == 1:
        return actual_outputs[0]
    if len(actual_outputs) == len(all_cases):
        return actual_outputs[case_index]

    raise ContractError(
        "ambiguous_actual_output_mapping:tc=%s outputs=%d cases=%d"
        % (case.get("tc_id", "unknown"), len(actual_outputs), len(all_cases))
    )


def ensure_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
        return [item.strip().strip("'\"") for item in text.split(",") if item.strip()]
    return [text]


def ensure_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def canonical_grader_name(name: str) -> str:
    raw = str(name or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in GRADER_ALIASES:
        return GRADER_ALIASES[raw]
    return raw


def parse_weight_map(value: Any) -> Dict[str, float]:
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                value = {}
    if not isinstance(value, dict):
        return {}
    out: Dict[str, float] = {}
    for key, item in value.items():
        try:
            out[canonical_grader_name(str(key))] = float(item)
        except (TypeError, ValueError):
            continue
    return out


def parse_threshold_map(value: Any) -> Dict[str, float]:
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                value = {}
    if not isinstance(value, dict):
        return {}
    out: Dict[str, float] = {}
    for key, item in value.items():
        try:
            out[canonical_grader_name(str(key))] = float(item)
        except (TypeError, ValueError):
            continue
    return out


def parse_grader_selection(case: Dict[str, Any], query: str, reference_response: str) -> List[str]:
    judge_payload = ensure_dict(case.get("judge_payload"))
    raw = (
        judge_payload.get("grader_selection")
        or judge_payload.get("graders")
        or case.get("grader_selection")
        or case.get("grader_plan")
    )

    selected: List[str] = []
    if isinstance(raw, dict):
        selected = ensure_list(raw.get("selected") or raw.get("graders"))
        if not selected:
            for key, enabled in raw.items():
                if isinstance(enabled, bool) and enabled:
                    selected.append(str(key))
    else:
        selected = ensure_list(raw)

    if selected:
        normalized: List[str] = []
        for item in selected:
            name = canonical_grader_name(item)
            if name not in SUPPORTED_GRADERS:
                raise ContractError("unsupported_grader:%s" % item)
            if name not in normalized:
                normalized.append(name)
        return normalized

    # Default dynamic plan inferred from testcase content.
    inferred = ["relevance", "correctness"]
    signal_text = " ".join(
        [
            str(case.get("title", "")),
            str(case.get("expected", "")),
            " ".join(ensure_list(case.get("expected_conditions"))),
            str(query or ""),
            str(reference_response or ""),
        ]
    ).lower()
    if "json" in signal_text:
        inferred.append("json_validator")
        if str(reference_response or "").strip().startswith("{") or str(reference_response or "").strip().startswith("["):
            inferred.append("json_match")
    if "instruction" in signal_text or "format" in signal_text or "constraint" in signal_text:
        inferred.append("instruction_following")
    if "safety" in signal_text or "harm" in signal_text:
        inferred.append("harmfulness")
    if reference_response:
        inferred.append("hallucination")

    deduped: List[str] = []
    for item in inferred:
        if item not in deduped:
            deduped.append(item)
    return deduped


def get_grader_score(result_payload: Dict[str, Any]) -> float:
    try:
        return float(result_payload.get("score", 0.0))
    except (TypeError, ValueError):
        return 0.0


def normalize_score(grader_name: str, score: float) -> float:
    if grader_name in LLM_SCORE_GRADERS:
        normalized = score / 5.0
    else:
        normalized = score
    if normalized < 0.0:
        return 0.0
    if normalized > 1.0:
        return 1.0
    return normalized


def run_async(coro: Any) -> Any:
    return asyncio.run(coro)


def dump_result(result: Any) -> Dict[str, Any]:
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    return {"value": str(result)}


def has_transient_error(exc: Exception) -> bool:
    text = str(exc).lower()
    markers = [
        "timeout",
        "timed out",
        "rate limit",
        "temporarily unavailable",
        "connection",
        "503",
        "429",
    ]
    return any(marker in text for marker in markers)


def compact_error_text(error_text: str, limit: int = 200) -> str:
    compacted = " ".join(str(error_text or "").split())
    if len(compacted) <= limit:
        return compacted
    return compacted[:limit] + "..."


def extract_grader_error(result_payload: Dict[str, Any]) -> str:
    direct_error = result_payload.get("error")
    if isinstance(direct_error, str) and direct_error.strip():
        return direct_error.strip()
    metadata = result_payload.get("metadata")
    if isinstance(metadata, dict):
        meta_error = metadata.get("error")
        if isinstance(meta_error, str) and meta_error.strip():
            return meta_error.strip()
    return ""


def classify_judge_error(error_text: str) -> str:
    lowered = str(error_text or "").lower()
    if any(marker in lowered for marker in JUDGE_ERROR_MODEL_UNSUPPORTED_MARKERS):
        return "model_unsupported"
    if any(marker in lowered for marker in JUDGE_ERROR_AUTH_MARKERS):
        return "auth"
    if any(marker in lowered for marker in JUDGE_ERROR_INVALID_REQUEST_MARKERS):
        return "invalid_request"
    if has_transient_error(Exception(lowered)):
        return "transient"
    return "runtime"


def raise_for_grader_error(grader_name: str, error_text: str, llm_config: Dict[str, Any]) -> None:
    category = classify_judge_error(error_text)
    summary = compact_error_text(error_text)
    model = str(llm_config.get("model", "")).strip()

    if category == "transient":
        raise TransientJudgeError("judge_transient_error:%s:%s" % (grader_name, summary))
    if category == "model_unsupported":
        raise ContractError("judge_model_unsupported:%s:%s" % (model or "unknown_model", summary))
    if category == "auth":
        raise ContractError("judge_auth_error:%s" % summary)
    if category == "invalid_request":
        raise ContractError("judge_invalid_request:%s" % summary)
    raise RuntimeError("judge_runtime_error:%s:%s" % (grader_name, summary))


def create_openai_model(llm_config: Dict[str, Any]) -> OpenAIChatModel:
    return OpenAIChatModel(
        model=llm_config["model"],
        api_key=llm_config["api_key"],
        base_url=llm_config.get("base_url"),
    )


def parse_llm_config(args: argparse.Namespace, case: Dict[str, Any]) -> Dict[str, Any]:
    judge_payload = case.get("judge_payload", {})
    if not isinstance(judge_payload, dict):
        judge_payload = {}

    model = str(
        judge_payload.get("judge_model")
        or args.judge_model
        or os.environ.get("ANC_QA_JUDGE_MODEL", "")
        or "gpt-5.3-codex"
    ).strip()
    base_url = str(
        judge_payload.get("judge_base_url")
        or args.judge_base_url
        or os.environ.get("OPENAI_BASE_URL", "")
    ).strip()
    api_key_env = str(args.judge_api_key_env or "OPENAI_API_KEY").strip() or "OPENAI_API_KEY"
    api_key = os.environ.get(api_key_env, "")

    if not model:
        raise ContractError("missing_judge_model")
    if not api_key:
        raise ContractError("missing_judge_api_key_env:%s" % api_key_env)

    return {
        "model": model,
        "base_url": base_url or None,
        "api_key": api_key,
        "llm_threshold": args.llm_threshold,
        "default_grader_threshold_llm": args.default_grader_threshold_llm,
        "default_grader_threshold_binary": args.default_grader_threshold_binary,
    }


def evaluate_exact_match(reference_text: str, response_text: str) -> Dict[str, Any]:
    grader = StringMatchGrader(
        name="exact_match",
        algorithm="exact_match",
        case_sensitive=False,
        ignore_whitespace=True,
    )
    result = run_async(
        grader.aevaluate(reference_response=reference_text, response=response_text)
    )
    payload = dump_result(result)
    score = float(payload.get("score", 0.0))
    decision = "pass" if score >= 1.0 else "fail"
    return {
        "decision": decision,
        "score": score,
        "result": payload,
    }


def evaluate_rule_match(expected_conditions: List[str], response_text: str) -> Dict[str, Any]:
    if not expected_conditions:
        raise ContractError("rule_match_missing_expected_conditions")
    grader = StringMatchGrader(
        name="contains_all",
        algorithm="contains_all",
        case_sensitive=False,
    )
    result = run_async(
        grader.aevaluate(reference_response="", response=response_text, substrings=expected_conditions)
    )
    payload = dump_result(result)
    score = float(payload.get("score", 0.0))
    decision = "pass" if score >= 1.0 else "fail"
    return {
        "decision": decision,
        "score": score,
        "result": payload,
    }


def evaluate_llm_judge(
    case: Dict[str, Any],
    response_text: str,
    llm_config: Dict[str, Any],
    max_concurrency: int,
) -> Dict[str, Any]:
    judge_payload = case.get("judge_payload", {})
    if not isinstance(judge_payload, dict):
        judge_payload = {}

    expected_conditions = ensure_list(judge_payload.get("expected_conditions")) or ensure_list(
        case.get("expected_conditions")
    )
    reference_response = normalize_text(
        judge_payload.get("reference_response")
        or judge_payload.get("expected_output")
        or case.get("expected")
        or "\n".join(expected_conditions)
    )
    query = normalize_text(
        judge_payload.get("objective")
        or case.get("objective_ref")
        or case.get("title")
    )
    context = normalize_text(
        judge_payload.get("context")
        or case.get("spec_ref")
    )
    instruction = normalize_text(
        judge_payload.get("instruction")
        or "\n".join(expected_conditions)
        or case.get("title")
    )

    try:
        model = create_openai_model(llm_config)

        selected_graders = parse_grader_selection(
            case=case,
            query=query,
            reference_response=reference_response,
        )
        weight_map = parse_weight_map(
            judge_payload.get("grader_weights")
            or case.get("grader_weights")
        )
        threshold_map = parse_threshold_map(
            judge_payload.get("min_score_per_grader")
            or case.get("min_score_per_grader")
        )
        must_pass = [
            canonical_grader_name(item)
            for item in ensure_list(judge_payload.get("must_pass_graders") or case.get("must_pass_graders"))
        ]

        grader_configs: Dict[str, Dict[str, Any]] = {}
        # Keep per-grader algorithm settings for deterministic graders.
        similarity_algorithm = str(judge_payload.get("similarity_algorithm", "rougeL")).strip() or "rougeL"
        string_match_algorithm = str(judge_payload.get("string_match_algorithm", "contains_all")).strip() or "contains_all"

        for grader_name in selected_graders:
            if grader_name == "relevance":
                grader_configs[grader_name] = {
                    "grader": RelevanceGrader(model=model, threshold=3),
                    "mapper": {
                        "query": "query",
                        "response": "response",
                        "reference_response": "reference_response",
                        "context": "context",
                    },
                }
            elif grader_name == "correctness":
                grader_configs[grader_name] = {
                    "grader": CorrectnessGrader(model=model, threshold=3),
                    "mapper": {
                        "query": "query",
                        "response": "response",
                        "reference_response": "reference_response",
                        "context": "context",
                    },
                }
            elif grader_name == "hallucination":
                grader_configs[grader_name] = {
                    "grader": HallucinationGrader(model=model, threshold=3),
                    "mapper": {
                        "query": "query",
                        "response": "response",
                        "reference_response": "reference_response",
                        "context": "context",
                    },
                }
            elif grader_name == "instruction_following":
                grader_configs[grader_name] = {
                    "grader": InstructionFollowingGrader(model=model, threshold=3),
                    "mapper": {
                        "instruction": "instruction",
                        "query": "query",
                        "response": "response",
                    },
                }
            elif grader_name == "harmfulness":
                grader_configs[grader_name] = {
                    "grader": HarmfulnessGrader(model=model, threshold=3),
                    "mapper": {
                        "query": "query",
                        "response": "response",
                        "reference_response": "reference_response",
                        "context": "context",
                    },
                }
            elif grader_name == "json_validator":
                grader_configs[grader_name] = {
                    "grader": JsonValidatorGrader(name="json_validator"),
                    "mapper": {
                        "response": "response",
                    },
                }
            elif grader_name == "json_match":
                grader_configs[grader_name] = {
                    "grader": JsonMatchGrader(name="json_match", strict_order=False, ignore_extra_keys=False),
                    "mapper": {
                        "reference_response": "reference_response",
                        "response": "response",
                    },
                }
            elif grader_name == "string_match":
                grader_configs[grader_name] = {
                    "grader": StringMatchGrader(
                        name="string_match",
                        algorithm=string_match_algorithm,
                        case_sensitive=False,
                    ),
                    "mapper": {
                        "reference_response": "reference_response",
                        "response": "response",
                    },
                }
            elif grader_name == "similarity":
                grader_configs[grader_name] = {
                    "grader": SimilarityGrader(algorithm=similarity_algorithm),
                    "mapper": {
                        "reference_response": "reference_response",
                        "response": "response",
                    },
                }
            elif grader_name == "auto_rubric":
                task_description = normalize_text(
                    judge_payload.get("auto_rubric_task_description")
                    or judge_payload.get("objective")
                    or case.get("title")
                )
                if not task_description:
                    raise ContractError("auto_rubric_missing_task_description")
                scenario = normalize_text(
                    judge_payload.get("auto_rubric_scenario")
                    or case.get("spec_ref")
                )
                sample_queries = ensure_list(judge_payload.get("auto_rubric_sample_queries")) or [query]
                generator = SimpleRubricsGenerator(
                    SimpleRubricsGeneratorConfig(
                        grader_name="auto_rubric",
                        model=model,
                        grader_mode=GraderMode.POINTWISE,
                        task_description=task_description,
                        scenario=scenario,
                        min_score=1,
                        max_score=5,
                    )
                )
                auto_grader = run_async(
                    generator.generate(dataset=[{"query": query}], sample_queries=sample_queries)
                )
                grader_configs[grader_name] = {
                    "grader": auto_grader,
                    "mapper": {
                        "query": "query",
                        "response": "response",
                    },
                }
            else:
                raise ContractError("unsupported_grader:%s" % grader_name)

        runner = GradingRunner(
            grader_configs=grader_configs,
            max_concurrency=max_concurrency,
            show_progress=False,
        )

        dataset = [
            {
                "query": query,
                "response": response_text,
                "reference_response": reference_response,
                "context": context,
                "instruction": instruction,
            }
        ]
        results = run_async(runner.arun(dataset))

        if not must_pass:
            must_pass = list(grader_configs.keys())

        normalized_weight_sum = 0.0
        weighted_total = 0.0
        grader_results: Dict[str, Dict[str, Any]] = {}
        must_pass_violations: List[str] = []

        for grader_name in grader_configs.keys():
            result_payload = dump_result(results[grader_name][0])
            grader_error = extract_grader_error(result_payload)
            if grader_error:
                raise_for_grader_error(grader_name=grader_name, error_text=grader_error, llm_config=llm_config)
            raw_score = get_grader_score(result_payload)
            normalized = normalize_score(grader_name, raw_score)
            weight = weight_map.get(grader_name, 1.0)
            if weight <= 0:
                raise ContractError("invalid_grader_weight:%s" % grader_name)

            if grader_name in threshold_map:
                threshold = threshold_map[grader_name]
            elif grader_name in LLM_SCORE_GRADERS:
                threshold = llm_config.get("default_grader_threshold_llm", 3.0)
            else:
                threshold = llm_config.get("default_grader_threshold_binary", 1.0)

            pass_check = raw_score >= float(threshold)
            if grader_name in must_pass and not pass_check:
                must_pass_violations.append(grader_name)

            weighted_total += normalized * weight
            normalized_weight_sum += weight
            grader_results[grader_name] = {
                "score": raw_score,
                "normalized_score": normalized,
                "threshold": threshold,
                "passed": pass_check,
                "weight": weight,
                "result": result_payload,
            }

        if normalized_weight_sum <= 0:
            raise ContractError("invalid_grader_weights")

        overall_score_0_1 = weighted_total / normalized_weight_sum
        overall_score = overall_score_0_1 * 5.0
        threshold = float(llm_config.get("llm_threshold", 3.0))
        decision = "pass" if overall_score >= threshold and not must_pass_violations else "fail"

        return {
            "decision": decision,
            "score": overall_score,
            "result": {
                "query": query,
                "reference_response": reference_response,
                "graders": grader_results,
                "selected_graders": list(grader_configs.keys()),
                "must_pass_graders": must_pass,
                "must_pass_violations": must_pass_violations,
                "overall_normalized_score": overall_score_0_1,
                "threshold": threshold,
            },
        }
    except Exception as exc:
        if has_transient_error(exc):
            raise TransientJudgeError(str(exc)) from exc
        raise


def score_case(
    case: Dict[str, Any],
    response_text: str,
    args: argparse.Namespace,
) -> Dict[str, Any]:
    method = str(case.get("evaluation_method", "Rule Match")).strip().lower()
    expected_text = normalize_text(case.get("expected"))
    expected_conditions = ensure_list(case.get("expected_conditions"))

    if method == "exact match":
        return evaluate_exact_match(expected_text, response_text)
    if method == "rule match":
        return evaluate_rule_match(expected_conditions, response_text)
    if method in {"llm-judge", "human review"}:
        llm_config = parse_llm_config(args, case)
        return evaluate_llm_judge(
            case=case,
            response_text=response_text,
            llm_config=llm_config,
            max_concurrency=args.max_concurrency,
        )

    raise ContractError("unsupported_evaluation_method:%s" % method)


def aggregate_case_decisions(case_results: List[Dict[str, Any]], pre_contract_invalid: bool) -> str:
    if pre_contract_invalid:
        return "test_invalid"
    decisions = [item.get("decision") for item in case_results]
    if any(decision == "fail" for decision in decisions):
        return "fail"
    if any(decision == "hold" for decision in decisions):
        return "hold"
    if any(decision == "test_invalid" for decision in decisions):
        return "test_invalid"
    return "pass"


def run_objective_or_regression(
    mode: str,
    datapoints: List[Dict[str, Any]],
    actual_outputs: List[Dict[str, Any]],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    case_results: List[Dict[str, Any]] = []
    reasons: List[str] = []
    pre_contract_invalid = False

    for idx, case in enumerate(datapoints):
        tc_id = case.get("tc_id", "unknown")
        try:
            output_obj = resolve_case_output(case, idx, datapoints, actual_outputs)
            scored = score_case(case, output_obj["text"], args)
            case_result = {
                "tc_id": tc_id,
                "priority": case.get("priority", ""),
                "evaluation_method": case.get("evaluation_method"),
                "actual_output_ref": output_obj["ref"],
                "decision": scored["decision"],
                "score": scored.get("score"),
                "result": scored["result"],
            }
            case_results.append(case_result)
            if scored["decision"] != "pass":
                reasons.append("%s:%s" % (tc_id, scored["decision"]))
        except ContractError as exc:
            pre_contract_invalid = True
            case_results.append(
                {
                    "tc_id": tc_id,
                    "priority": case.get("priority", ""),
                    "evaluation_method": case.get("evaluation_method"),
                    "decision": "test_invalid",
                    "error": str(exc),
                }
            )
            reasons.append("%s:test_invalid:%s" % (tc_id, str(exc)))
        except TransientJudgeError as exc:
            case_results.append(
                {
                    "tc_id": tc_id,
                    "priority": case.get("priority", ""),
                    "evaluation_method": case.get("evaluation_method"),
                    "decision": "hold",
                    "error": str(exc),
                }
            )
            reasons.append("%s:hold" % tc_id)
        except Exception as exc:
            case_results.append(
                {
                    "tc_id": tc_id,
                    "priority": case.get("priority", ""),
                    "evaluation_method": case.get("evaluation_method"),
                    "decision": "fail",
                    "error": str(exc),
                }
            )
            reasons.append("%s:fail" % tc_id)

    decision = aggregate_case_decisions(case_results, pre_contract_invalid)
    return {
        "evaluation_verdict": decision,
        "gate_decision": decision,
        "case_results": case_results,
        "reasons": reasons or ["all_cases_passed"],
        "mode": mode,
    }


def resolve_subjective_outputs(
    case: Dict[str, Any],
    case_index: int,
    case_count: int,
    actual_outputs: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    judge_payload = case.get("judge_payload", {})
    if isinstance(judge_payload, dict):
        baseline_ref = clean_ref(judge_payload.get("baseline_output_ref", ""))
        candidate_ref = clean_ref(judge_payload.get("candidate_output_ref", ""))
        if baseline_ref and candidate_ref:
            return load_output_ref(Path(baseline_ref)), load_output_ref(Path(candidate_ref))

    if len(actual_outputs) == 2:
        return actual_outputs[0], actual_outputs[1]
    if len(actual_outputs) == case_count * 2:
        return actual_outputs[case_index * 2], actual_outputs[(case_index * 2) + 1]

    raise ContractError(
        "subjective_mode_requires_two_variants:tc=%s outputs=%d"
        % (case.get("tc_id", "unknown"), len(actual_outputs))
    )


def parse_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    if value is None:
        return default
    text = str(value)
    digits = "".join([ch for ch in text if ch.isdigit()])
    if not digits:
        return default
    return int(digits)


def build_subjective_llm_grader(
    case: Dict[str, Any],
    llm_config: Dict[str, Any],
    query: str,
    context: str,
    expected_conditions: List[str],
) -> Any:
    judge_payload = ensure_dict(case.get("judge_payload"))
    model = create_openai_model(llm_config)
    task_description = normalize_text(
        judge_payload.get("subjective_auto_rubric_task_description")
        or judge_payload.get("auto_rubric_task_description")
        or ""
    )
    use_auto_rubric = str(
        judge_payload.get("subjective_use_auto_rubric")
        or judge_payload.get("use_auto_rubric")
        or ""
    ).strip().lower() in {"1", "true", "yes", "on"}
    if task_description:
        use_auto_rubric = True

    if use_auto_rubric:
        if not task_description:
            task_description = query
        scenario = normalize_text(
            judge_payload.get("subjective_auto_rubric_scenario")
            or judge_payload.get("auto_rubric_scenario")
            or context
        )
        sample_queries = ensure_list(judge_payload.get("auto_rubric_sample_queries")) or [query]
        generator = SimpleRubricsGenerator(
            SimpleRubricsGeneratorConfig(
                grader_name="subjective_pairwise_rubric",
                model=model,
                grader_mode=GraderMode.LISTWISE,
                task_description=task_description,
                scenario=scenario,
                min_score=1,
                max_score=2,
            )
        )
        return run_async(
            generator.generate(
                dataset=[{"query": query}],
                sample_queries=sample_queries,
            )
        )

    rubric_lines = (
        ensure_list(judge_payload.get("subjective_rubrics"))
        or ensure_list(judge_payload.get("rubrics"))
        or expected_conditions
        or [
            "objective alignment",
            "spec compliance",
            "usefulness and clarity",
        ]
    )
    rubric_text = "\n".join(["- %s" % item for item in rubric_lines])
    template = """
You are a strict QA evaluator for ANC quality gate subjective A/B testing.
Task objective:
{query}

Spec context:
{context}

Expected conditions:
{expected_conditions}

Rubric:
{rubric_text}

Compare two candidate responses and rank them from best to worst.
Response 1:
{response_1}

Response 2:
{response_2}

Return JSON only:
{{
  "rank": [<rank_for_response_1>, <rank_for_response_2>],
  "reason": "<concise rationale>"
}}

Rules:
- rank must be a permutation of [1,2]
- smaller rank means better quality
- no tie allowed
"""
    return LLMGrader(
        name="subjective_pairwise",
        mode=GraderMode.LISTWISE,
        model=model,
        template=template,
    )


def evaluate_subjective_pair(
    case: Dict[str, Any],
    response_x: str,
    response_y: str,
    args: argparse.Namespace,
) -> Dict[str, Any]:
    method = str(case.get("evaluation_method", "Rule Match")).strip().lower()
    if method not in {"llm-judge", "human review"}:
        scored_x = score_case(case, response_x, args)
        scored_y = score_case(case, response_y, args)
        x_score = float(scored_x.get("score", 0.0))
        y_score = float(scored_y.get("score", 0.0))
        winner_side = "tie"
        if x_score > y_score:
            winner_side = "x"
        elif y_score > x_score:
            winner_side = "y"
        return {
            "winner_side": winner_side,
            "scores": {"x": x_score, "y": y_score},
            "judge_result": {
                "mode": "pointwise_compare",
                "x": scored_x,
                "y": scored_y,
            },
        }

    judge_payload = ensure_dict(case.get("judge_payload"))
    expected_conditions = ensure_list(judge_payload.get("expected_conditions")) or ensure_list(
        case.get("expected_conditions")
    )
    query = normalize_text(
        judge_payload.get("objective")
        or case.get("objective_ref")
        or case.get("title")
    )
    context = normalize_text(
        judge_payload.get("context")
        or case.get("spec_ref")
    )
    llm_config = parse_llm_config(args, case)
    grader = build_subjective_llm_grader(
        case=case,
        llm_config=llm_config,
        query=query,
        context=context,
        expected_conditions=expected_conditions,
    )

    try:
        result = run_async(
            grader.aevaluate(
                query=query,
                context=context,
                expected_conditions="\n".join(expected_conditions),
                rubric_text="\n".join(expected_conditions),
                response_1=response_x,
                response_2=response_y,
            )
        )
    except Exception as exc:
        if has_transient_error(exc):
            raise TransientJudgeError("subjective_transient_error:%s" % compact_error_text(str(exc))) from exc
        raise_for_grader_error(grader_name=grader.name, error_text=str(exc), llm_config=llm_config)
        raise
    payload = dump_result(result)
    grader_error = extract_grader_error(payload)
    if grader_error:
        raise_for_grader_error(grader_name=grader.name, error_text=grader_error, llm_config=llm_config)

    rank = payload.get("rank")
    if not isinstance(rank, list) or len(rank) != 2:
        raise ContractError("subjective_invalid_rank:%s" % rank)
    try:
        rank_x = int(rank[0])
        rank_y = int(rank[1])
    except (TypeError, ValueError) as exc:
        raise ContractError("subjective_invalid_rank:%s" % rank) from exc
    if {rank_x, rank_y} != {1, 2}:
        raise ContractError("subjective_invalid_rank:%s" % rank)

    winner_side = "x" if rank_x < rank_y else "y"
    return {
        "winner_side": winner_side,
        "scores": {"x": 1.0 if winner_side == "x" else 0.0, "y": 1.0 if winner_side == "y" else 0.0},
        "judge_result": payload,
    }


def run_subjective(
    datapoints: List[Dict[str, Any]],
    compile_meta: Dict[str, Any],
    actual_outputs: List[Dict[str, Any]],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    eval_cfg = compile_meta.get("evaluation_configuration", {}) if isinstance(compile_meta, dict) else {}
    rounds = args.subjective_rounds
    if rounds is None:
        rounds = parse_int(eval_cfg.get("subjective_eval_rounds"), default=9)
    if rounds <= 0:
        raise ContractError("invalid_subjective_rounds")

    seed = args.seed
    if seed is None:
        seed = parse_int(eval_cfg.get("subjective_seed") or eval_cfg.get("seed"), default=42)
    rng = random.Random(seed)

    baseline_wins = 0
    candidate_wins = 0
    ties = 0
    comparisons: List[Dict[str, Any]] = []
    reasons: List[str] = []
    pre_contract_invalid = False

    for case_idx, case in enumerate(datapoints):
        tc_id = case.get("tc_id", "unknown")
        try:
            judge_payload = ensure_dict(case.get("judge_payload"))
            baseline_output, candidate_output = resolve_subjective_outputs(
                case=case,
                case_index=case_idx,
                case_count=len(datapoints),
                actual_outputs=actual_outputs,
            )
            case_rounds = parse_int(
                judge_payload.get("subjective_rounds")
                or judge_payload.get("rounds"),
                default=rounds,
            )
            if case_rounds <= 0:
                raise ContractError("invalid_subjective_rounds:%s" % tc_id)

            for round_idx in range(1, case_rounds + 1):
                blind_flip = rng.choice([True, False])
                x_variant = "candidate" if blind_flip else "baseline"
                y_variant = "baseline" if blind_flip else "candidate"
                x_output = candidate_output if x_variant == "candidate" else baseline_output
                y_output = baseline_output if y_variant == "baseline" else candidate_output

                pair_eval = evaluate_subjective_pair(
                    case=case,
                    response_x=x_output["text"],
                    response_y=y_output["text"],
                    args=args,
                )
                winner_side = pair_eval.get("winner_side", "tie")
                if winner_side == "x":
                    winner = x_variant
                elif winner_side == "y":
                    winner = y_variant
                else:
                    winner = "tie"

                if winner == "candidate":
                    candidate_wins += 1
                elif winner == "baseline":
                    baseline_wins += 1
                else:
                    ties += 1

                comparisons.append(
                    {
                        "tc_id": tc_id,
                        "round": round_idx,
                        "seed": seed,
                        "blind_assignment": {
                            "x": x_variant,
                            "y": y_variant,
                        },
                        "scores": {
                            "baseline": pair_eval.get("scores", {}).get(
                                "x" if x_variant == "baseline" else "y",
                                0.0,
                            ),
                            "candidate": pair_eval.get("scores", {}).get(
                                "x" if x_variant == "candidate" else "y",
                                0.0,
                            ),
                        },
                        "winner": winner,
                        "judge_result": pair_eval.get("judge_result"),
                    }
                )
        except ContractError as exc:
            pre_contract_invalid = True
            reasons.append("%s:test_invalid:%s" % (tc_id, exc))
        except TransientJudgeError as exc:
            reasons.append("%s:hold:%s" % (tc_id, exc))
        except Exception as exc:
            reasons.append("%s:fail:%s" % (tc_id, exc))

    if pre_contract_invalid:
        decision = "test_invalid"
        subjective_verdict = "review"
        win_rate = 0.0
    elif any(":fail:" in reason for reason in reasons):
        decision = "fail"
        subjective_verdict = "reject"
        win_rate = 0.0
    elif any(":hold:" in reason for reason in reasons):
        decision = "hold"
        subjective_verdict = "review"
        win_rate = 0.0
    else:
        non_tie_total = baseline_wins + candidate_wins
        win_rate = 0.5 if non_tie_total == 0 else (candidate_wins / float(non_tie_total))
        if win_rate >= (2.0 / 3.0):
            subjective_verdict = "accept"
            decision = "pass"
        elif win_rate < 0.5:
            subjective_verdict = "reject"
            decision = "fail"
        else:
            subjective_verdict = "review"
            decision = "hold"

    return {
        "evaluation_verdict": decision,
        "gate_decision": decision,
        "subjective_verdict": subjective_verdict,
        "win_rate": win_rate,
        "seed": seed,
        "rounds": rounds,
        "baseline_wins": baseline_wins,
        "candidate_wins": candidate_wins,
        "ties": ties,
        "comparisons": comparisons,
        "reasons": reasons or ["subjective_completed"],
    }


def run(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_eval_ref = out_dir / "raw_eval.json"
    runner_log_ref = out_dir / "runner.log"
    execution_state_ref = out_dir / "execution_state.json"

    started_at = now_utc()
    execution_state: Dict[str, Any] = {
        "state": "running",
        "mode": args.mode,
        "module": args.module,
        "started_at": started_at,
        "progress_signals": {
            "log_delta": True,
            "phase_progress": "bundle_loaded",
            "output_heartbeat": True,
        },
    }

    try:
        if args.mode not in VALID_MODES:
            raise ContractError("invalid_mode:%s" % args.mode)

        bundle_path = Path(args.preparation_bundle)
        runtime = parse_preparation_bundle(bundle_path)

        datapoints = runtime["datapoints"]
        compile_meta = runtime.get("compile_meta", {})

        if not args.actual_output:
            raise ContractError("missing_actual_output")
        actual_outputs = [load_output_ref(Path(ref)) for ref in args.actual_output]

        if args.mode in {"objective", "regression"}:
            run_result = run_objective_or_regression(
                mode=args.mode,
                datapoints=datapoints,
                actual_outputs=actual_outputs,
                args=args,
            )
        else:
            run_result = run_subjective(
                datapoints=datapoints,
                compile_meta=compile_meta,
                actual_outputs=actual_outputs,
                args=args,
            )

        gate_decision = run_result["gate_decision"]
        if gate_decision not in VALID_DECISIONS:
            raise ContractError("invalid_gate_decision:%s" % gate_decision)

        raw_payload = {
            "mode": args.mode,
            "module": args.module,
            "preparation_bundle_ref": str(bundle_path),
            "actual_output_refs": [item["ref"] for item in actual_outputs],
            "run": run_result,
            "timestamp": now_utc(),
        }
        write_json(raw_eval_ref, raw_payload)

        execution_state.update(
            {
                "state": "completed",
                "completed_at": now_utc(),
                "decision": gate_decision,
                "case_count": len(datapoints),
            }
        )
        write_json(execution_state_ref, execution_state)

        runner_log_ref.write_text(
            "mode=%s module=%s decision=%s\n" % (args.mode, args.module, gate_decision),
            encoding="utf-8",
        )

        payload = {
            "raw_eval_ref": str(raw_eval_ref),
            "runner_log_ref": str(runner_log_ref),
            "execution_state_ref": str(execution_state_ref),
            "evaluation_verdict": gate_decision,
            "gate_decision": gate_decision,
            "evidence_ref": str(out_dir),
            "reasons": run_result.get("reasons", ["completed"]),
            "profile_id": runtime.get("profile_ids", [""])[0] if runtime.get("profile_ids") else "",
            "retry_hint": "retry" if gate_decision == "hold" else "",
            "raw_eval_summary": {
                "mode": args.mode,
                "case_count": len(datapoints),
            },
        }
        if args.mode == "subjective":
            payload["subjective_verdict"] = run_result.get("subjective_verdict")
            payload["win_rate"] = run_result.get("win_rate")
            payload["seed"] = run_result.get("seed")
            payload["rounds"] = run_result.get("rounds")

        print(json.dumps(payload, ensure_ascii=True))
        return code_for(gate_decision)

    except ContractError as exc:
        failure = {
            "error": str(exc),
            "mode": args.mode,
            "module": args.module,
            "timestamp": now_utc(),
        }
        write_json(raw_eval_ref, failure)
        execution_state.update(
            {
                "state": "rejected",
                "completed_at": now_utc(),
                "decision": "test_invalid",
                "error": str(exc),
            }
        )
        write_json(execution_state_ref, execution_state)
        runner_log_ref.write_text("contract_error=%s\n" % exc, encoding="utf-8")
        payload = {
            "raw_eval_ref": str(raw_eval_ref),
            "runner_log_ref": str(runner_log_ref),
            "execution_state_ref": str(execution_state_ref),
            "evaluation_verdict": "test_invalid",
            "gate_decision": "test_invalid",
            "evidence_ref": str(out_dir),
            "reasons": ["contract_error", str(exc)],
        }
        print(json.dumps(payload, ensure_ascii=True))
        return 20
    except Exception as exc:
        failure = {
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "mode": args.mode,
            "module": args.module,
            "timestamp": now_utc(),
        }
        write_json(raw_eval_ref, failure)
        execution_state.update(
            {
                "state": "failed",
                "completed_at": now_utc(),
                "decision": "fail",
                "error": str(exc),
            }
        )
        write_json(execution_state_ref, execution_state)
        runner_log_ref.write_text("exception=%s\n" % exc, encoding="utf-8")
        payload = {
            "raw_eval_ref": str(raw_eval_ref),
            "runner_log_ref": str(runner_log_ref),
            "execution_state_ref": str(execution_state_ref),
            "evaluation_verdict": "fail",
            "gate_decision": "fail",
            "evidence_ref": str(out_dir),
            "reasons": ["exception", str(exc)],
        }
        print(json.dumps(payload, ensure_ascii=True))
        return 50


def main() -> int:
    parser = argparse.ArgumentParser(prog="quality_eval_runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--preparation-bundle", required=True)
    run_parser.add_argument("--mode", required=True)
    run_parser.add_argument("--actual-output", action="append", default=[])
    run_parser.add_argument("--module", default="M1")
    run_parser.add_argument("--output-dir", required=True)
    run_parser.add_argument("--judge-model", default="gpt-5.3-codex")
    run_parser.add_argument("--judge-base-url", default="")
    run_parser.add_argument("--judge-api-key-env", default="OPENAI_API_KEY")
    run_parser.add_argument("--subjective-rounds", type=int, default=None)
    run_parser.add_argument("--seed", type=int, default=None)
    run_parser.add_argument("--llm-threshold", type=float, default=3.0)
    run_parser.add_argument("--default-grader-threshold-llm", type=float, default=3.0)
    run_parser.add_argument("--default-grader-threshold-binary", type=float, default=1.0)
    run_parser.add_argument("--max-concurrency", type=int, default=4)

    args = parser.parse_args()
    if args.command == "run":
        return run(args)
    return 50


if __name__ == "__main__":
    raise SystemExit(main())
