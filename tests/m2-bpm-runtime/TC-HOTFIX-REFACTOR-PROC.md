# TC-HOTFIX-PROC-001 / TC-REFACTOR-PROC-001

## TC-HOTFIX-PROC-001 hotfix 主流程真实分发验证

- 目标: 验证 `hotfix` 在真实 OpenClaw 分发下可完成 7 个 phase 协作链路。
- 输入: `tests/m2-bpm-runtime/run_tc_hotfix_refactor_proc.py` 自动构造的 hotfix incident/asset 上下文。
- 期望:
  - `processes/meta/hotfix/scripts/hotfix_runner.py` 返回 `status=ok`
  - `phase_count=7`
  - 每个 phase `dispatch.executed=true` 且 `return_code=0`
  - `session_id == actual_session_id`
  - 同 Actor 跨 phase 会话隔离生效（`architect p1!=p2`、`qa p3!=p5`、`admin p6!=p7`）
- 失败策略: 任一 phase 分发失败、会话不一致或输出引用缺失即 Fail-Closed。

## TC-REFACTOR-PROC-001 refactor 主流程真实分发验证

- 目标: 验证 `refactor` 在真实 OpenClaw 分发下可完成 6 个 phase 协作链路。
- 输入: `tests/m2-bpm-runtime/run_tc_hotfix_refactor_proc.py` 自动构造的 objective/tech debt/asset 上下文。
- 期望:
  - `processes/meta/refactor/scripts/refactor_runner.py` 返回 `status=ok`
  - `phase_count=6`
  - 每个 phase `dispatch.executed=true` 且 `return_code=0`
  - `session_id == actual_session_id`
  - 同 Actor 跨 phase 会话隔离生效（`architect p1!=p2`、`qa p3!=p5`）
- 失败策略: 任一 phase 分发失败、会话不一致或输出引用缺失即 Fail-Closed。

## 执行入口

- `python3 tests/m2-bpm-runtime/run_tc_hotfix_refactor_proc.py`
