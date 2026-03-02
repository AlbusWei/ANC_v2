# development-process 流程设计

> 版本: v0.1.1 | 分类: Meta Process | 层级: P4 | process_id: development-process | process_type: dev.prototype | 生命周期: review | 最后更新: 2026-03-02

## 目标

`development-process` 是 `M3` 的最小可复用开发闭环，用于在不引入 release/evolution 开销的前提下，完成从 Objective 到 Lifecycle 的可执行治理收口。

它在系统主线中的位置是：

`Objective -> Spec -> Test -> Implement -> Verify -> Lifecycle`

## 连续性与 phase 闭合

1. 本流程覆盖开发连续段与最小生命周期治理段，不覆盖 release/evolution。
2. phase 全部映射已注册子流程，禁止未定义 phase：
   - `objective-scope-baseline`
   - `spec-authoring-contract`
   - `quality-gate-preparation`
   - `implementation-execution-core`
   - `quality-gate-evaluation`
   - `lifecycle-review`
3. 开发失败只允许在 `p5 -> p4` 回路内迭代，禁止无界回退。

## 义务映射（Development Loop Core Standard）

1. O1 Objective -> `p1`
2. O2 Spec -> `p2`
3. O3 Test -> `p3`
4. O4 Implement -> `p4`
5. O5 Verify -> `p5`
6. O6 Lifecycle -> `p6`

约束：

1. `process_type` 固定为 `dev.prototype`，必须遵循 `docs/design/processes/development-loop-core-standard.md`。
2. 任一义务缺失或证据不可追溯时，Fail-Closed。

## 输入契约

1. `objective_context_ref`
2. `target_asset_ref`
3. `requested_transition`
4. `superpower_ref`（必填，贯通 p3/p5/p6 上下文）

## 输出契约

1. `objective_ref`
2. `scope_baseline_ref`
3. `spec_ref`
4. `test_plan_ref`
5. `implementation_ref`
6. `final_gate_verdict_ref`
7. `lifecycle_transition_ref`
8. `registry_sync_ref`

## 阶段定义

1. `p1 objective-scope-baseline`
   - actor: `architect`
   - 输出：`objective_ref` + `scope_baseline_ref`
2. `p2 spec-authoring-contract`
   - actor: `architect`
   - 输出：`spec_ref`
3. `p3 quality-gate-preparation`
   - actor: `qa`
   - 输出：`test_plan_ref`
4. `p4 implementation-execution-core`
   - actor: `kernel-dev`
   - 输出：`implementation_ref`
5. `p5 quality-gate-evaluation`
   - actor: `qa`
   - 输出：`final_gate_verdict_ref`
6. `p6 lifecycle-gate-sync`
   - actor: `hr`
   - 输出：`lifecycle_transition_ref` + `registry_sync_ref`

## 控制流

`p1 -> p2 -> p3 -> p4 -> p5`

1. `p5` 失败：`p5 -> p4`（条件：`iterations < 2`）。
2. `p5` 成功且 `gate_decision == pass`：`p5 -> p6`。
3. `p6` 成功：`p6 -> end`。

## Fail-Closed

1. Objective/Spec/Test 任一输入不可达或不可解析。
2. 门禁结论非 `pass` 时禁止进入 lifecycle。
3. `lifecycle-review` 输出不完整（缺 `lifecycle_transition_ref` 或 `registry_sync_ref`）。
4. 证据链断裂或 rule_refs 不可追溯。
5. `superpower_ref` 缺失或不可达。
