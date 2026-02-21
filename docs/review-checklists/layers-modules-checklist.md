# Layers & Modules Review Checklist

> Branch: `codex/review-layers-modules`
> Worktree: `review-layers-modules`

## 1. 目标

核对 L0~L5 与 M1~M6 的定义、依赖方向与工程化最小标准一致性。

## 2. Entire 执行要求（每次会话）

1. `entire status --detailed`
2. `.../entire_codex_bridge.py start`
3. 每回合改动后 `sync`
4. commit 后检查 `Entire-Checkpoint`
5. `.../entire_codex_bridge.py end`

## 3. 允许修改范围

1. `docs/design/layers/`
2. `docs/design/modules/`

## 4. 禁止修改范围

1. `docs/design/data-models/`
2. `docs/design/interfaces/`
3. `docs/design/business/`

## 5. 核对项

1. 每层都满足七类定义（Agents/Skills/Processes/Components/Interfaces/Data Models/Acceptance）。
2. 层间依赖方向符合上层依赖下层。
3. `layer-interface-contracts.md` 与当前 schema/流程语义一致。
4. 模块依赖矩阵反映本轮新增对象与现实建设顺序。
5. 模块关键路径与风险说明可执行。
6. L5 双主线交付模型与 L3/L4 复用关系清晰。

## 6. 完成定义（DoD）

1. 形成“层/模块一致性差异清单”并关闭。
2. `layer-interface-contracts.md` 与 `module-dependency-matrix.md` 不再停留旧版语义。
3. 提交仅包含 layers/modules 文件。

## 7. 建议提交粒度

1. `layers: interface contract refresh`
2. `modules: dependency matrix and phase mapping refresh`

## 8. M1 实施待办清单（Post-Design）

### 实施顺序（skills -> atomic processes -> composite processes -> agents -> integration）

1. S0 基线准备
   - 固化 `quality_eval_runner` CLI 协议与返回码（0/20/30/40/50）。
   - 准备证据目录模板：preparation bundle / eval outputs / hold governance。
2. S1 技能实现（先单点可测，再串联）
   - `sys.qa.test-compiler`（含 profile-binding mode）。
   - `sys.qa.evaluation-runner`（objective/subjective/regression 三 mode）。
   - `sys.qa.verdict-normalizer`。
   - `sys.qa.hold-triage`。
   - `sys.qa.regression-runner`。
3. S2 原子流程落地（按依赖从前到后）
   - AP-018 -> AP-019 -> AP-020。
   - AP-021 -> AP-022 -> AP-023 -> AP-024 -> AP-025。
   - 回归修订 AP-005/AP-006/AP-007/AP-008/AP-009 的执行脚手架。
4. S3 复合流程编排
   - `quality-gate-preparation`（输出唯一 `preparation_bundle_ref`）。
   - `quality-gate-evaluation`（消费 bundle + actual outputs）。
   - `hold-governance`（仅由 hold 路由触发）。
5. S4 Agent 接线与职责落盘
   - QA: AP-018/019/020/021/022/023 执行主责。
   - BPM: AP-024/025 与升级链执行主责。
   - Admin: hold 升级终点与治理裁决。
6. S5 集成验收
   - E2E 顺序：preparation -> AP-006 -> evaluation -> hold-governance（条件触发）。
   - 失败路径：test_invalid / hold / fail 全覆盖。
   - 通过 `registry_contract_tool.py verify` + 关键链路 dry-run 证据包验收。

### 里程碑门禁

1. G1（Skill Gate）：5 个 quality gate skills 均有可执行最小实现与 TEST 证据。
2. G2（Atomic Gate）：AP-018~AP-025 全部具备可回放 I/O 证据。
3. G3（Process Gate）：三个复合流程可被 BPM 连续调度。
4. G4（Reuse Gate）：M3/M4/M5 至少各 1 条链路复用通过。
