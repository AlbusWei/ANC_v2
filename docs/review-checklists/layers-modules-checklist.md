# Layers & Modules Review Checklist

> Branch: `codex/review-layers-modules`
> Worktree: `/Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules`
> Baseline Commit: `d2d7699`

## 1. 目标

核对 L0~L5 与 M1~M6 的边界、依赖与治理门禁定义是否与当前 SSOT 和施工平面一致。

## 2. SSOT 绑定

1. `/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/design/layers/layer-interface-contracts.md`
4. `/Users/albus/MyProjects/ANC_v2/docs/design/modules/module-dependency-matrix.md`
5. `/Users/albus/MyProjects/ANC_v2/docs/architecture/construction_plane.md`

## 3. 当前进度（d2d7699）

- [x] 模块依赖矩阵已升级为类型化依赖（R/G/T/E）并与关键路径对齐。
- [x] Trigger governance 文档链路已补齐（proposal/checklist/evidence）。
- [x] M1 质量门禁设计已闭环到 `quality-gate-preparation`、`quality-gate-evaluation`、`hold-governance`。
- [x] AP-018 ~ AP-025 原子流程文档已落盘并接入 P6 目录。
- [ ] M2 trigger runtime 可执行资产仍未落地（当前以文档与证据模板为主）。
- [ ] M3/M4/M5 的运行级复用证据仍待补齐。

## 4. 核对项

- [ ] 每层都包含 7 类定义（Agents/Skills/Processes/Components/Interfaces/Data Models/Acceptance）。
- [ ] 层间依赖方向严格遵循上层依赖下层，无逆向运行时依赖。
- [ ] `layer-interface-contracts.md` 与 process/data/interface 实际字段一致。
- [ ] `module-dependency-matrix.md` 的风险项都对应到可执行缓解动作。
- [ ] M1/M2/M4 的 trigger 与 lifecycle 边界不重叠。

## 5. 完成定义（DoD）

- [ ] 形成“层/模块一致性差异清单”并关闭。
- [ ] 至少 1 条 M1 -> M2 -> M4 的链路有运行级证据。
- [ ] `registry_contract_tool.py verify` 持续通过。

## 6. 提交前校验

1. `entire status --detailed`
2. `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py sync --prompt "..." --summary "..." --files ...`
3. `python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify`
4. `git log -1 --pretty=raw`（确认 `Entire-Checkpoint`）
