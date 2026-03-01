# M1 OpenJudge Adapter 规范

> 版本: v0.2.0 | 状态: draft | 最后更新: 2026-02-21

## 1. 目标与范围

本规范定义 `M1` 与 OpenJudge 的适配契约，确保：

1. `TEST.md` 作为唯一测试上游定义被稳定编译。
2. `superpower_ref` 作为 SDD→TDD 协同主键必须随 preparation/evaluation 输入传递且可追溯。
3. OpenJudge 仅输出 `raw eval`。
4. `M1 adapter` 统一输出 `unified verdict` 并提供 `gate_decision`。
5. 证据链可被 `M2` 与 `M4` 审计消费。

非目标：

1. 不在本规范定义生命周期状态推进（由 `M4` 负责）。
2. 不在本规范定义流程状态机（由 `M2` 负责）。

## 2. 体系边界

执行边界固定为：

`OpenJudge (eval execution) -> M1 adapter (gate computation) -> M2 (runtime state) -> M4 (lifecycle state)`

## 2.1 必需技能与流程（设计约束）

必需技能设计：

1. `/Users/albus/MyProjects/ANC_v2/docs/design/skills/quality-gate-skills.md`

必需复合流程设计：

1. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/quality-gate-preparation-process.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/quality-gate-evaluation-process.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/hold-governance-process.md`

## 3. 准备包契约（Preparation Bundle）

`quality-gate-preparation` 的唯一主输出为 `preparation_bundle_ref`。

`preparation_bundle` 索引最小字段：

1. `objective_ref`
2. `spec_ref`
3. `test_doc_ref`
4. `test_datapoints_ref`
5. `tc_profile_map_ref`
6. `compile_report_ref`
7. `producer_process_id`
8. `timestamps`

## 4. CLI 契约（quality_eval_runner）

统一入口（供 `M2` 调用）：

```bash
quality_eval_runner run \
  --preparation-bundle <absolute-path-or-ref> \
  --mode <objective|subjective|regression> \
  --actual-output <absolute-path-or-ref> \
  --module <M3|M4|M5|...> \
  --output-dir <absolute-path>
```

运行返回码约定：

1. `0`: 执行成功并输出分项评测结果。
2. `20`: `test_invalid`（编译或运行前契约错误）。
3. `30`: `hold`（仍在有效运行或待 triage）。
4. `40`: `fail`（Fail-Closed 触发）。
5. `50`: 系统级执行异常（需 triage）。

## 5. 输出契约

### 5.1 raw eval（OpenJudge）

由 OpenJudge 原生格式产出，完整保留原文。

### 5.2 unified verdict（M1 adapter）

必填字段：

```json
{
  "gate_decision": "pass|fail|test_invalid",
  "runtime_gate_state": "pass|fail|hold|test_invalid",
  "evidence_ref": "path/to/evidence/package",
  "reasons": ["..."]
}
```

可选白名单：

```json
{
  "raw_eval_ref": "path/to/raw_eval.json",
  "retry_hint": "retry|debug|manual-check",
  "profile_id": "quality-gate.baseline@1.0.0",
  "parser_notes": "..."
}
```

## 6. 分项评测与总聚合

1. AP-007：客观评测，输出 `objective_eval_ref`。
2. AP-008：主观评测，输出 `subjective_eval_ref`（可选）。
3. AP-009：回归评测，输出 `regression_eval_ref`。
4. AP-020：汇总分项评测结果，输出最终 `gate_decision + runtime_gate_state`。

聚合规则：

1. 任一 P0 `fail` -> 总体 `fail`
2. 无 `fail` 且存在 `hold` -> `runtime_gate_state=hold`，对外 `gate_decision=fail`
3. 其他 -> 总体 `pass`

## 7. HOLD 治理规则（无硬超时）

1. 长时运行不直接触发失败。
2. `runtime_gate_state=hold` 必须进入 `hold-governance`。
3. triage 基于三类进展信号：日志增量、阶段状态推进、输出流心跳。
4. triage 决策限定：`continue/retry/debug/fail`。
5. `hold -> fail` 仅在确认异常或无进展证据时触发。
6. 对外发布路径不消费 `hold`，只消费 `gate_decision=pass|fail|test_invalid`。

## 8. 证据包规范

`evidence_ref` 指向单一目录，目录内必须含索引文件。建议结构：

```text
<evidence_package>/
  index.json
  unified_verdict.json
  preparation/
    preparation_bundle.index.json
  raw_eval/
    objective.json
    subjective.json
    regression.json
  summaries/
    objective-redacted.md
    regression-redacted.md
  logs/
    runner.log
```

索引最小字段：

1. `run_id`
2. `profile_id`
3. `input_refs`
4. `raw_eval_ref`
5. `gate_decision`
6. `reasons`
7. `actor`
8. `timestamps`

## 9. Profile 治理

1. profile 采用语义化版本并登记 registry。
2. baseline profile 为默认源，模块仅覆盖差异。
3. 可变范围仅限：grader 组合、轮次、重试、证据附加项。
4. 不可改项：
   - `gate_decision` 枚举
   - Unified Verdict 必填字段
   - Fail-Closed 主规则

## 10. 分阶段实施

1. PoC：AP-007 的 1 个 P0 套件跑通。
2. Pilot：覆盖 `M3/M4/M5` 并验证模块 profile 差异。
3. Gate-on：门禁生效 + 模块复用 + 审计可追溯同时满足。
