## Context

本变更处于 M1 运行收口回合的 Thread-0，目标是建立后续 Thread-1~5 的唯一对齐源与证据基线。实现顺序必须遵循 `Objective -> Spec -> Test -> Development`，并按 Fail-Closed 处理证据缺失、协议不一致或 Entire trailer 缺失。

已知前置（由 M2 完成并直接继承）:

1. QA 三流程（`quality-gate-preparation`、`quality-gate-evaluation`、`hold-governance`）已在 inventory/registry 进入 `review`。
2. `runtime-policy-calibration` 已进入 `review` 且具备可执行 runner。
3. `system-analyst` 已进入已注册 Agent 清单并处于 `review`。
4. `verify-m2` 已存在，M2 W5 收口语义已落盘。

## Goals / Non-Goals

**Goals**

1. 建立 `m1-quality-gate-runtime-closure` 的 OpenSpec change 与三件套。
2. 落盘 Thread-0~5 分拆计划，定义每线程目标、输入、输出、依赖、验收标准。
3. 初始化 M6 本轮证据目录，固化 `round_id` 与 `openspec_ref`。
4. 固化每线程“至少 1 次 Entire sync + 1 次独立提交”的提交策略。

**Non-Goals**

1. 不在 Thread-0 实施任何 Thread-1~5 的功能改造。
2. 不重复执行已由 M2 完成的流程/Agent review 推进与 `verify-m2` 能力建设。
3. 不在本线程推进生命周期状态到 `active`。

## Decisions

### Decision 1: Thread-Plan 作为唯一对齐源

- Choice: 将 `thread-plan.md` 设为 Thread-0~5 的唯一执行对齐源，后续线程仅在该文件定义的边界内推进。
- Rationale: 避免多文档并行演化导致范围漂移和验收口径不一致。
- Alternative considered: 让每个线程独立维护各自计划。Rejected，因跨线程依赖与交接成本不可控。

### Decision 2: 先落盘再改造

- Choice: Thread-0 仅完成 OpenSpec 与 M6 证据基座，不进入功能实现。
- Rationale: 在范围、依赖和 DoD 未统一前执行代码改造会放大返工风险。
- Alternative considered: Thread-0 直接做部分实现。Rejected，违反“基座先行”的门禁策略。

### Decision 3: 强制线程级 Entire/Commit 最小动作

- Choice: 每线程至少 1 次 `entire_codex_bridge.py sync` + 1 次独立提交 + trailer 校验。
- Rationale: 保证每个线程都可独立审计，支持 checkpoint/commit 对账。
- Alternative considered: 仅在最终线程执行一次 sync。Rejected，无法满足线程粒度追溯。

## Dependency Graph

`Thread-0 -> Thread-1 -> Thread-2 -> Thread-3 -> Thread-4 -> Thread-5`

- 所有线程串行推进，禁止跨线程并提。
- 线程切换前必须具备交接物与验收结论。

## Risks / Trade-offs

1. [Risk] Thread-1~5 执行时偏离 Thread-0 计划。
   - Mitigation: 把 `thread-plan.md` 作为唯一对齐源，若需变更必须在新回合显式修订并记录。
2. [Risk] 提交遗漏 `Entire-Checkpoint` trailer。
   - Mitigation: 每线程提交后固定执行 `git log -1 --pretty=raw` 校验，不满足即 Fail-Closed。
3. [Risk] 重复消耗在 M2 已完成事项上。
   - Mitigation: 在 proposal/design/tasks 与 thread-plan 同步声明“不重复执行清单”。

## Open Questions

1. Thread-1 的差距清单采用“按链路”还是“按资产”主视图输出，是否需要双视图并行。
2. Thread-4 回归阶段若发现跨线程历史缺口，是否允许回写 Thread-2/3 文档后再进入 Thread-5 收口。

