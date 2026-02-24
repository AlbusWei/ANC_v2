# Thread-1 Gap Baseline（补齐版）

## 元信息

- round_id: `R-20260222-M6-m1-quality-gate-runtime-closure-01`
- openspec_ref: `m1-quality-gate-runtime-closure`
- baseline_owner: `architect`
- baseline_scope: `M1 运行收口（仅差距识别，不重复 M2 已完成事项）`

## 输入证据

1. `openspec/changes/m1-quality-gate-runtime-closure/thread-plan.md`
2. `runtime_data/execution/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/round-evidence.jsonl`
3. `runtime_data/execution/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/round_close_summary.md`
4. `runtime_data/execution/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/thread_handoff.md`
5. `docs/architecture/construction_plane.md`

## 差距清单（主链路/异常链路/Fail-Closed/回退链路）

| gap_id | 链路类型 | 差距描述 | 当前状态 | 优先级 |
|---|---|---|---|---|
| G-01 | 主链路 | OpenSpec change 缺少 `specs/**` delta 与 `Scenario`，`validate` 失败，导致 change 无法归档 | 本轮已补齐并待校验归档 | P0 |
| G-02 | 异常链路 | `validate` 失败后的责任人/时限未显式固化，导致 `needs_sync` 可长期悬挂 | 本轮通过任务闭合，后续纳入治理节奏 | P1 |
| G-03 | Fail-Closed | trailer 抽检若使用图遍历命令会引入范围外提交，审计边界易漂移 | 已切换为 `--no-walk` 定点抽检 | P1 |
| G-04 | 回退链路 | `review -> active` 观测窗口与回滚演练尚未形成闭环证据 | 保留为下一轮准入前置条件 | P1 |

## 不重复执行清单（继承 M2）

1. QA 三流程进入 `review` 的注册与首轮运行级落盘。
2. `runtime-policy-calibration` 进入 `review` 的注册与基础链路。
3. `system-analyst` 进入 `review` 的注册。
4. `verify-m2` 能力建设与 W5 语义收口。

## Thread-2 可执行输入（从本基线导出）

1. G-01: 补齐 OpenSpec delta + Scenario，并使 `openspec validate` 通过。
2. G-02: 在 `tasks.md/design.md` 中显式记录 carryover 闭合动作与状态迁移条件。
3. G-03: 固化提交审计命令为 `git log --pretty=raw --no-walk <sha...>`。
4. G-04: 明确保留项为“下一轮 active 准入门槛”，不在本轮夸大 Done。
