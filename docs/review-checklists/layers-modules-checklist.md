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
