# TC-M5-001~007 与 TC-M5-HOOK-001~004

## 主链与异常链（TC-M5-001~007）

1. `TC-M5-001`：主链 happy path（`m3.implementation.completed` 进入 `trigger-event-runtime` 并落触发回执）
2. `TC-M5-002`：升级阈值命中（`m1.gate.failed` 触发升级）
3. `TC-M5-003`：缺失证据 Fail-Closed（`missing_transition_evidence_ref`）
4. `TC-M5-004`：证据不可达 Fail-Closed（`transition_evidence_unreachable`）
5. `TC-M5-005`：策略未命中必须落 `unmatched_event_receipt`
6. `TC-M5-006`：去重冲突不可判定 Fail-Closed（`dedupe_conflict_unresolved`）
7. `TC-M5-007`：重复事件拒绝（`dedupe_decision=reject`）

## Hook 专项（TC-M5-HOOK-001~004）

1. `TC-M5-HOOK-001`：平台事件 happy path（`trigger_source=platform-hook` 可进入运行时并落回执）
2. `TC-M5-HOOK-002`：平台事件缺证据 Fail-Closed
3. `TC-M5-HOOK-003`：平台事件去重冲突 Fail-Closed
4. `TC-M5-HOOK-004`：平台事件未命中策略必须落回执

## 执行入口

1. `python3 -m pytest tests/m5-self-evolution/test_m5_admission_regression.py -q`
2. `python3 -m pytest tests/m5-self-evolution/test_hook_bridge_pack.py -q`
3. `python3 tests/m5-self-evolution/run_tc_online.py`
