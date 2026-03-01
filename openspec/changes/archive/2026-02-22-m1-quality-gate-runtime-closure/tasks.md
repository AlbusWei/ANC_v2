## 0. 全局约束（Thread-0~5）

- [x] 0.1 固定 `round_id = R-20260222-M6-m1-quality-gate-runtime-closure-01`。
- [x] 0.2 固定 `openspec_ref = m1-quality-gate-runtime-closure`。
- [x] 0.3 明确“不重复执行已由 M2 完成事项”。
- [x] 0.4 每个线程至少完成 1 次 Entire sync + 1 次独立提交，并校验 `Entire-Checkpoint` trailer。

## 1. Thread-0 基座初始化（当前线程）

- [x] 1.1 初始化/复用 change 目录：`openspec/changes/m1-quality-gate-runtime-closure/`。
- [x] 1.2 新增 `thread-plan.md`，落盘 Thread-0~5 分拆执行总计划。
- [x] 1.3 更新 `proposal.md`、`design.md`、`tasks.md` 三件套。
- [x] 1.4 初始化证据目录 `runtime_data/execution/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/` 并至少包含：
  - `scope_baseline.md`
  - `open_questions.md`
  - `round-evidence.jsonl`（含 `round_open`）
  - `thread_handoff.md`

依赖关系：无。

DoD:

- OpenSpec 与证据目录文件齐全，内容可读且字段一致。
- 本线程不进入 Thread-1~5 功能改造。

## 2. Thread-1 差距基线锁定

- [x] 2.1 基于 Thread-0 计划输出 M1 运行收口差距清单。（见 `thread-1-gap-baseline.md`）
- [x] 2.2 明确主链路、异常链路、Fail-Closed、回退路径的缺口与优先级。（见 `thread-1-gap-baseline.md`）
- [x] 2.3 产出 Thread-2 可执行输入清单。

依赖关系：Thread-0 完成并提交。

DoD:

- 差距清单可直接驱动 Thread-2 契约落盘。
- 清单内显式排除 M2 已完成事项。

## 3. Thread-2 设计与契约落盘

- [x] 3.1 将 Thread-1 差距项映射到设计/契约文档。
- [x] 3.2 更新 OpenSpec 设计与任务拆解，使 Thread-3 有明确实现范围。
- [x] 3.3 记录线程交接物与风险清单。

依赖关系：Thread-1 完成并提交。

DoD:

- 每个差距项都有对应文档变更与可追溯链接。
- 无超范围改造目标混入。

## 4. Thread-3 最小实现改造

- [x] 4.1 按 Thread-2 锁定范围实施最小实现。
- [x] 4.2 增补必要测试与 Fail-Closed 分支验证。
- [x] 4.3 输出 Thread-4 回归输入（测试入口、已知风险、回退路径）。

依赖关系：Thread-2 完成并提交。

DoD:

- 核心链路可运行。
- 异常路径可触发 Fail-Closed 且有证据。

## 5. Thread-4 回归与稳定性校准

- [x] 5.1 执行回归并记录关键现象、风险判断与是否满足准入。
- [x] 5.2 对未通过项做最小修正并保持独立提交。
- [x] 5.3 形成 Thread-5 收口输入包。

依赖关系：Thread-3 完成并提交。

DoD:

- 关键场景回归通过，异常路径可恢复/可回退。
- 输出包含自然语言结论，不仅是原始日志。

## 6. Thread-5 收口与状态对齐

- [x] 6.1 汇总 Thread-0~4 证据并完成 OpenSpec 收口说明。
- [x] 6.2 同步施工平面对应条目并确保状态一致。
- [x] 6.3 完成最终门禁核验，未满足则 Fail-Closed。

依赖关系：Thread-4 完成并提交。

DoD:

- OpenSpec、施工平面、证据链三方一致。
- 线程级 checkpoint/commit 可对账且无缺口。
