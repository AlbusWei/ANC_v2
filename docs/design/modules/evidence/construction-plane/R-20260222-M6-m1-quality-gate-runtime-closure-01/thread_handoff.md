# Thread Handoff

## 元信息

- round_id: `R-20260222-M6-m1-quality-gate-runtime-closure-01`
- openspec_ref: `m1-quality-gate-runtime-closure`
- handoff_owner: `architect`

## 线程顺序

`Thread-0 -> Thread-1 -> Thread-2 -> Thread-3 -> Thread-4 -> Thread-5`

## 交接物清单

### Thread-0 -> Thread-1

- `openspec/changes/m1-quality-gate-runtime-closure/thread-plan.md`
- `openspec/changes/m1-quality-gate-runtime-closure/proposal.md`
- `openspec/changes/m1-quality-gate-runtime-closure/design.md`
- `openspec/changes/m1-quality-gate-runtime-closure/tasks.md`
- `docs/design/modules/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/scope_baseline.md`
- `docs/design/modules/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/open_questions.md`

### Thread-1 -> Thread-2（计划）

- `openspec/changes/m1-quality-gate-runtime-closure/thread-1-gap-baseline.md`（由 Thread-1 新增）
- Thread-1 风险与优先级清单（写入本目录新增证据文件）

### Thread-2 -> Thread-3（计划）

- Thread-2 设计/契约变更列表
- Thread-3 开发任务拆解与边界清单

### Thread-3 -> Thread-4（计划）

- 实现增量路径清单
- 回归输入、失败分支证据、已知风险

### Thread-4 -> Thread-5（计划）

- 回归结论
- 待收口事项与最终门禁输入

## 交接规则

1. 未完成本线程 DoD，禁止移交下线程。
2. 每次移交前必须完成当线程 Entire sync + 独立提交 + trailer 校验。
3. 若发现缺失交接物，按 Fail-Closed 停止推进并补齐。

## Thread-1 更新（2026-02-22）

### 已完成产出（接线重构 + 文档同步）

1. M3 三条主流程由 QA skill 直连改为复用质量门禁子流程：
   - `processes/meta/full-development/process.json`
   - `processes/meta/hotfix/process.json`
   - `processes/meta/refactor/process.json`
2. 三条主流程的 `p3/p5` 统一改为：
   - `p3 -> subprocess: quality-gate-preparation`
   - `p5 -> subprocess: quality-gate-evaluation`
3. 三条主流程 `composed_processes` 已补齐为：
   - `quality-gate-preparation`
   - `quality-gate-evaluation`
4. 人工指引文档与 manifest 已对齐：
   - `processes/meta/full-development/PROCESS.md`
   - `processes/meta/hotfix/PROCESS.md`
   - `processes/meta/refactor/PROCESS.md`
5. 设计文档 phase->流程映射已改为子流程平台化口径：
   - `docs/design/processes/full-development-process.md`
   - `docs/design/processes/hotfix-process.md`
   - `docs/design/processes/refactor-process.md`

### Thread-2 必读输入

1. `openspec/changes/m1-quality-gate-runtime-closure/thread-plan.md`
2. `openspec/changes/m1-quality-gate-runtime-closure/tasks.md`
3. `docs/design/modules/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/thread_handoff.md`
4. `processes/meta/full-development/process.json`
5. `processes/meta/hotfix/process.json`
6. `processes/meta/refactor/process.json`
7. `docs/design/processes/full-development-process.md`
8. `docs/design/processes/hotfix-process.md`
9. `docs/design/processes/refactor-process.md`

### 未完成依赖（交由 Thread-2/后续线程闭合）

1. `openspec/changes/m1-quality-gate-runtime-closure/thread-1-gap-baseline.md` 尚未创建（本线程按约束仅做接线重构 + 文档同步）。
2. Thread-1 风险与优先级清单证据文件尚未在本目录新增，需要后续线程补齐并回填交接引用。

## Thread-2 更新（2026-02-22）

### 已完成产出（lifecycle-review 最小可执行资产）

1. 新增流程资产目录：`processes/meta/lifecycle-review/`
   - `SKILL.md`
   - `PROCESS.md`
   - `process.json`
   - `scripts/lifecycle_review_runner.py`
2. 新增流程设计文档：`docs/design/processes/lifecycle-review-process.md`
3. 注册表与清单联动：
   - `shared/registry/process_registry.json` 新增 `lifecycle-review`（`status=draft`，`owner=hr`）
   - `docs/design/inventories/process-inventory.md` 新增 canonical path 与已注册条目
   - `docs/design/processes/governance-processes.md` 更新为可执行资产口径
   - `docs/design/modules/M4-lifecycle-management.md` 增加 M1->M4 接点说明
   - `docs/architecture/construction_plane.md` 同步 Next/Done 条目

### Thread-3 可调用入口（最小示例）

1. 执行命令：
   - `python3 processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py --input docs/design/modules/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/thread3_lifecycle_review_input.json --output docs/design/modules/evidence/construction-plane/R-20260222-M6-m1-quality-gate-runtime-closure-01/thread3_lifecycle_review_output.json`
2. 输入文件最小字段（`thread3_lifecycle_review_input.json`）：
   - `final_gate_verdict_ref`
   - `target_asset_ref`
   - `requested_transition`

### 交接边界（Thread-2 -> Thread-3）

1. 本线程仅提供 `lifecycle-review` 最小可执行资产，不处理 M3 接线。
2. 本线程不落运行证据，Thread-3 负责实跑与证据沉淀，并基于证据评估是否推进生命周期状态。
