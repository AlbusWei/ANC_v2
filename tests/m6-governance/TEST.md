# m6-governance-round6 - Test Cases

## Objective Alignment

补测 `M6` 开发成果在真实运行链路下的可执行性、Fail-Closed 行为与证据可追溯性，并验证 LLM-as-Judge 通道在凭据缺失时的阻断策略。

## Asset Coverage

1. `processes/meta/construction-plane-governance/scripts/run_round.py`
2. `processes/meta/construction-plane-governance/scripts/round_evidence_tool.py`
3. `skills/system/construction-audit/scripts/construction_audit.py`
4. `skills/system/openspec-sync/scripts/openspec_sync.sh`
5. `shared/registry/registry_contract_tool.py` (`verify` + `verify-m6`)
6. `skills/system/qa/test-compiler/scripts/compile_test_doc.py`
7. `skills/system/qa/evaluation-runner/scripts/quality_eval_runner`

## Test Cases

### TC-001: Registry 全局契约校验通过

- Type: Objective
- Priority: P0
- Input: `python3 shared/registry/registry_contract_tool.py verify`
- Expected: 返回码 `0` 且输出 `Verify passed`
- Evaluation Method: Rule Match

### TC-002: M6 场景 A 运行链路通过

- Type: Objective
- Priority: P0
- Input: `run_round.py --scenario A`
- Expected: 返回码 `0`，`round-result.json.status=passed`
- Evaluation Method: Exact Match

### TC-003: M6 场景 B 在 P5 对账阻断

- Type: Objective
- Priority: P0
- Input: `run_round.py --scenario B`
- Expected: 返回码 `1`，`failed_phase=p5`
- Evaluation Method: Exact Match

### TC-004: M6 场景 C 在 P4 同步冲突阻断

- Type: Objective
- Priority: P0
- Input: `run_round.py --scenario C`
- Expected: 返回码 `1`，`failed_phase=p4`
- Evaluation Method: Exact Match

### TC-005: verify-m6 对场景 A 判定通过

- Type: Objective
- Priority: P0
- Input: `verify-m6 --round-dir tmp/m6-round-regression-v2/A`
- Expected: 返回码 `0`
- Evaluation Method: Rule Match

### TC-006: verify-m6 对场景 B 判定阻断

- Type: Objective
- Priority: P0
- Input: `verify-m6 --round-dir tmp/m6-round-regression-v2/B`
- Expected: 返回码 `1` 且包含 `checkpoint_count must equal commit_count`
- Evaluation Method: Rule Match

### TC-007: verify-m6 对场景 C 判定阻断

- Type: Objective
- Priority: P0
- Input: `verify-m6 --round-dir tmp/m6-round-regression-v2/C`
- Expected: 返回码 `1` 且包含 `round_close must be the last event`
- Evaluation Method: Rule Match

### TC-008: construction-audit 支持仓库外绝对输出路径

- Type: Objective
- Priority: P0
- Input: `construction_audit.py --output /tmp/...`
- Expected: 返回码 `0` 且标准输出为绝对输出路径
- Evaluation Method: Exact Match

### TC-009: construction-audit 缺少 registry 范围时 Fail-Closed

- Type: Objective
- Priority: P0
- Input: `linkage_targets` 不含 `registry`
- Expected: 返回码 `3` 且输出 `decision=fail`
- Evaluation Method: Exact Match

### TC-010: openspec-sync checkpoint/commit 不一致阻断

- Type: Objective
- Priority: P0
- Input: `openspec_sync.sh` with `checkpoint_count != commit_count`
- Expected: 返回码 `15`
- Evaluation Method: Exact Match

### TC-011: M6 LLM 用例可被 test-compiler 编译

- Type: Objective
- Priority: P1
- Input: M6 专项 `TEST.md`（LLM-Judge）
- Expected: `compile_report.status=pass`
- Evaluation Method: Exact Match

### TC-012: LLM-as-Judge 可用时 objective 通过

- Type: Objective
- Priority: P0
- Input: `quality_eval_runner --judge-model gpt-5.3-codex`
- Expected: 返回码 `0`，`gate_decision=pass`
- Evaluation Method: Exact Match

### TC-013: LLM-as-Judge 无效模型时 Fail-Closed

- Type: Objective
- Priority: P0
- Input: `quality_eval_runner --judge-model <invalid-model>`
- Expected: 返回码 `20`，`gate_decision=test_invalid`
- Evaluation Method: Exact Match

## Evaluation Configuration

- Objective Eval Rounds: 1
- Subjective Eval Rounds: 0
- Judge Perspectives: [qa, architect]
- Timeout Seconds: 1800
- Retry Policy: max 1
