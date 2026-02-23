# M1 质量门禁运行收口（Thread-0~5）分拆执行总计划

## 元信息（唯一对齐源）

- round_id: `R-20260222-M6-m1-quality-gate-runtime-closure-01`
- openspec_ref: `m1-quality-gate-runtime-closure`
- change_name: `m1-quality-gate-runtime-closure`
- 本文角色: Thread-0~5 唯一对齐源（后续线程若与本文冲突，以本文为准并通过新回合显式修订）
- 本轮边界: 仅做基座初始化与分拆计划落盘，不在 Thread-0 执行后续功能改造

## 背景重基线（承接 M2 已完成事项）

1. QA 三流程已完成运行级落盘并进入 `review`：
   - `quality-gate-preparation`
   - `quality-gate-evaluation`
   - `hold-governance`
   证据来源：`docs/design/inventories/process-inventory.md`（W3-B 联动备注）。
2. `runtime-policy-calibration` 已注册为可执行流程并处于 `review`，且不在本轮推进 `active`。
3. `system-analyst` 已进入已注册 Agent 清单并处于 `review`。
4. `verify-m2` 专项校验能力已存在，且 M2 W5 已形成门禁收口语义（`verify/verify-m2/verify-m6` 与 post-dev regression 同回合通过）。

## 本轮 M1 剩余目标

1. 在不重复 M2 已完成工作的前提下，建立 M1 质量门禁运行收口的线程化执行基线。
2. 将 Thread-0~5 的输入/输出/依赖/验收标准固化为可审计计划，避免线程间目标漂移。
3. 明确每个线程的 Entire 与提交最小动作，确保 checkpoint/commit 可对账。
4. 为 Thread-1 提供可直接开工的输入清单与交接物。

## 线程分拆计划

### Thread-0（当前线程）

- 目标: 初始化 change 基座、三件套与 M6 本轮证据目录，落盘 Thread-0~5 总计划。
- 输入:
  - `AGENTS.md`
  - `docs/architecture/construction_plane.md`
  - `docs/design/inventories/process-inventory.md`
  - `docs/design/inventories/agent-inventory.md`
- 输出:
  - `openspec/changes/m1-quality-gate-runtime-closure/thread-plan.md`
  - `openspec/changes/m1-quality-gate-runtime-closure/proposal.md`
  - `openspec/changes/m1-quality-gate-runtime-closure/design.md`
  - `openspec/changes/m1-quality-gate-runtime-closure/tasks.md`
  - `docs/design/modules/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/{scope_baseline.md,open_questions.md,round-evidence.jsonl,thread_handoff.md}`
- 依赖: 无。
- 验收标准:
  - OpenSpec change 目录可见且包含三件套+计划。
  - `round-evidence.jsonl` 至少包含 1 条 `round_open` 事件，且 `openspec_ref` 固定为 `m1-quality-gate-runtime-closure`。
  - 完成 `registry verify`、`openspec list --json`、`git status --short` 校验并形成提交。

### Thread-1

- 目标: 形成 M1 运行收口“现状差距基线”，锁定后续改造范围与非目标边界。
- 输入:
  - `openspec/changes/m1-quality-gate-runtime-closure/thread-plan.md`
  - `openspec/changes/m1-quality-gate-runtime-closure/proposal.md`
  - `openspec/changes/m1-quality-gate-runtime-closure/design.md`
  - `docs/architecture/construction_plane.md`
  - `docs/design/modules/M1-test-system.md`
- 输出:
  - `openspec/changes/m1-quality-gate-runtime-closure/thread-1-gap-baseline.md`（新增）
  - 必要时更新 `openspec/changes/m1-quality-gate-runtime-closure/design.md` 的差距章节
- 依赖: Thread-0 完成并提交。
- 验收标准:
  - 差距清单覆盖主链路、异常链路、Fail-Closed 与回退链路。
  - 明确标注“不重复执行 M2 已完成事项”。
  - 给出 Thread-2 的可执行输入列表。

### Thread-2

- 目标: 完成与 Thread-1 差距对应的设计/契约落盘（仅文档与契约，不做大规模实现）。
- 输入:
  - `openspec/changes/m1-quality-gate-runtime-closure/thread-1-gap-baseline.md`
  - `docs/design/modules/M1-test-system.md`
  - `docs/design/processes/quality-gate-preparation-process.md`
  - `docs/design/processes/quality-gate-evaluation-process.md`
  - `docs/design/processes/hold-governance-process.md`
- 输出:
  - 变更后的设计文档与 OpenSpec 设计/任务拆解增量（路径由 Thread-1 差距清单确定）
  - 线程内交接记录（新增到证据目录）
- 依赖: Thread-1 完成并提交。
- 验收标准:
  - 设计变更与差距项一一对应，可追溯。
  - 仍保持“不重复执行 M2 已完成事项”的边界。
  - Thread-3 的开发目标和门禁输入清晰可执行。

### Thread-3

- 目标: 实施 M1 运行收口所需的最小实现改造（仅执行 Thread-2 锁定范围）。
- 输入:
  - Thread-2 锁定后的任务清单
  - 对应设计/契约文档
- 输出:
  - 代码与测试增量（以 Thread-2 锁定的路径为准）
  - 对应执行证据与失败分支记录
- 依赖: Thread-2 完成并提交。
- 验收标准:
  - 核心链路可运行，异常路径触发 Fail-Closed。
  - 不引入 Thread-2 范围之外的扩展改造。
  - 为 Thread-4 提供可复测输入与已知风险清单。

### Thread-4

- 目标: 完成回归与稳定性校准，验证收口改造具备可复现性。
- 输入:
  - Thread-3 代码与测试增量
  - Thread-3 风险清单
- 输出:
  - 回归结果记录与风险处置结论
  - 必要的修正提交（保持独立提交粒度）
- 依赖: Thread-3 完成并提交。
- 验收标准:
  - 关键场景可复测通过，异常路径可恢复/回退。
  - Fail-Closed 行为有证据可审计。
  - 为 Thread-5 提供收口所需的最终输入。

### Thread-5

- 目标: 完成变更收口与对齐归档（OpenSpec、施工平面、证据链）。
- 输入:
  - Thread-4 回归结论
  - 全线程提交与 checkpoint 对账信息
- 输出:
  - 更新后的 OpenSpec 状态与收口说明
  - 施工平面对应条目更新
  - 最终回合证据与交付摘要
- 依赖: Thread-4 完成并提交。
- 验收标准:
  - OpenSpec 与施工平面状态一致。
  - 线程证据、提交、checkpoint 三方可对账。
  - 未满足门禁则 Fail-Closed，禁止宣告 Done。

## 提交与同步策略（强制）

1. 每个 Thread 至少执行 1 次 Entire `sync`，且 `--files` 覆盖本线程实际改动文件。
2. 每个 Thread 至少产生 1 次独立提交（不可与其他 Thread 混提）。
3. 每次提交后必须执行 `git log -1 --pretty=raw`，确认包含 `Entire-Checkpoint: <id>` trailer。
4. 任一线程若出现 `start/sync/end` 失败、缺 trailer、或证据缺失，按 Fail-Closed 停止推进。

## 不重复执行清单（M2 已完成，M1 本轮不重做）

1. QA 三流程进入 `review` 的注册与首轮运行级落盘。
2. `runtime-policy-calibration` 进入 `review` 的注册与首轮端到端验证。
3. `system-analyst` 进入 `review` 的注册与基础协作链路落盘。
4. `verify-m2` 的能力创建与 M2 W5 语义收口。

