# TC-QA-PROC-001~003

## TC-QA-PROC-001 QA 主链路调度（Preparation -> Evaluation Pass）

- Input: 以 `TEST_rule.md` + baseline 实际输出运行 `quality-gate-preparation`，并将 `preparation_bundle_ref` 传入 `quality-gate-evaluation`。
- Expect:
  - `quality-gate-preparation` 返回 `verdict=pass` 且 `preparation_bundle_ref` 可追溯。
  - `quality-gate-evaluation` 返回 `gate_decision=pass`。
  - 证据链包含 `final_gate_verdict_ref` 与 `runtime_trace_ref`。

## TC-QA-PROC-002 Hold 分支路由（Runtime Hold -> hold-governance）

- Input: 在 `quality-gate-evaluation` 启用 `force_hold=true`，并提供 hold 治理最小输入。
- Expect:
  - `quality-gate-evaluation` 返回 `gate_decision=fail`、`runtime_gate_state=hold` 且 `hold_routed=true`。
  - `hold-governance` 子流程输出存在并包含 `hold_resolution_ref`。
  - hold 分支证据可达并可追溯到 triage 与 health-maintenance。

## TC-QA-PROC-003 自动回测闭环（Hold -> auto-retest -> Pass）

- Input: 在 `quality-gate-evaluation` 启用 `force_hold=true` 且设置 `max_auto_retest_cycles=1`，并提供 hold 治理最小输入。
- Expect:
  - 首轮进入 `runtime_gate_state=hold` 并路由 `hold-governance`。
  - `hold-governance` 返回 `retest_recommendation=auto-retest`。
  - 在预算内自动回测后返回 `gate_decision=pass`、`runtime_gate_state=pass`。
  - 输出中保留 `auto_retest_count=1` 与 hold 治理证据引用。
