# M1 Runtime Closure Test Entry

## Scope

本测试入口用于验证 `M3 -> M1 -> M4` 跨流程运行闭环在 Thread-3 的最小可执行能力，覆盖：

1. pass 主链路
2. fail-closed / test-invalid 阻断链路
3. hold 路由链路
4. `M5` 最小接入 `M1` 门禁入口
5. hold 自动回测闭环（`hold -> auto-retest -> pass`）
6. 真实用户服务语义评审链路（`LLM-as-Judge` + `QA agent` 缺陷发现与 debug 建议）

## Entrypoint

- Regression runner: `tests/m1-runtime/run_post_dev_regression.py`
- Evidence root: `tmp/runtime_data/execution/evidence/quality-gate/runtime-validation-round-6-m1-closure/`
- Semantic service runner: `tests/m1-runtime/run_semantic_service_validation.py`
- Semantic evidence root: `tmp/runtime_data/execution/evidence/quality-gate/runtime-validation-round-8-semantic-service/`

## Test Cases

### TC-M1-CHAIN-001 M3->M1->M4 pass

- Input:
  - 以 `quality-gate-preparation` 生成 `preparation_bundle_ref`
  - 以 `quality-gate-evaluation` 得到 `gate_decision=pass`
  - 以 `lifecycle-review` 执行 `review -> active`
- Expect:
  - `gate_decision=pass`
  - `lifecycle_transition_ref` 非空且可追溯
  - `registry_sync_ref` 非空且可追溯

### TC-M1-CHAIN-002 关键输入缺失触发 fail/test_invalid

- Input:
  - 缺失关键输入触发 `quality-gate-preparation` 的 `test_invalid`
  - 同回合验证 `lifecycle-review` 在缺失门禁证据时 Fail-Closed
- Expect:
  - `gate_decision=test_invalid`（或等价失败判定）
  - `lifecycle_transition_ref` 为空
  - 存在 `fail_closed_record_ref`

### TC-M1-CHAIN-003 evaluation hold 路由 hold-governance

- Input:
  - `quality-gate-evaluation` 设置 `force_hold=true`
- Expect:
  - `gate_decision=fail`
  - `runtime_gate_state=hold`
  - `hold_routed=true`
  - `hold_resolution_ref` 非空且可追溯

### TC-M1-CHAIN-004 M5 最小接入验证

- Input:
  - `M5` 改进请求通过 `M1` 门禁入口（preparation + evaluation）执行
- Expect:
  - `M5` 调用 `M1` 门禁入口可执行
  - `gate_decision=pass`

### TC-M1-CHAIN-005 hold 自动回测闭环

- Input:
  - `quality-gate-evaluation` 设置 `force_hold=true`
  - 设置 `max_auto_retest_cycles=1`
- Expect:
  - 首轮出现 `runtime_gate_state=hold` 并路由 `hold-governance`
  - `hold_retest_recommendation=auto-retest`
  - 回测后 `gate_decision=pass`、`runtime_gate_state=pass`
  - `auto_retest_count=1`

### TC-M1-SERVICE-001 真实服务语义评审（第一优先级主流程）

- Input:
  - 真实用户产品需求（owner=`hr`）
  - QA agent 基于需求产出测试设计
  - mock 开发交付（刻意缺失权限/审计/限流/测试证据）
- Expect:
  - BPM 流程实例创建、校验、回放证据可追溯
  - `quality_eval_runner` 使用 `LLM-Judge`（非 Rule Match）进行语义评测
  - 对 mock 交付输出阻断判定（`fail` 或 `hold`）
  - QA agent 输出缺陷清单与 debug 建议（非空）

## Fail-Closed Policy

1. 任一 runner 缺失或不可执行：立即失败。
2. 任一关键证据引用不可达：立即失败。
3. 未覆盖 `pass/fail-closed/hold` 三类判定证据：立即失败。

## Suggested Command

```bash
python3 tests/m1-runtime/run_post_dev_regression.py
python3 tests/m1-runtime/run_semantic_service_validation.py
```
