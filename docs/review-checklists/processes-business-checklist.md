# Processes & Business Review Checklist

> Branch: `codex/review-processes-business`
> Worktree: `/Users/albus/MyProjects/ANC_v2_worktrees/review-processes-business`
> Baseline Commit: `d2d7699`

## 1. 目标

核对 P1~P6、双主线业务流程与原子流程追溯关系，确保流程语法、义务模型和治理边界一致。

## 2. SSOT 绑定

1. `/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`
2. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/development-loop-core-standard.md`
3. `/Users/albus/MyProjects/ANC_v2/docs/design/processes/p4-p6-obligation-traceability-matrix.md`
4. `/Users/albus/MyProjects/ANC_v2/docs/design/business/internal-productization-e2e-flow.md`
5. `/Users/albus/MyProjects/ANC_v2/docs/design/business/software-vendor-e2e-flow.md`

## 3. 当前进度（d2d7699）

- [x] P4 双主线与 P6 原子流程映射已落盘。
- [x] 开发闭环义务模型与条件触发规则已集中到标准文档。
- [x] `quality-gate-preparation/evaluation/hold-governance` 复合流程文档已落盘。
- [x] AP-018 ~ AP-025 补齐并纳入流程目录。
- [ ] canonical/legacy 同名流程语义收敛仍有后续治理动作。
- [ ] 文档级证据已具备，运行级 dry-run 证据仍待持续补齐。

## 4. 核对项

- [ ] `phase -> subprocess` 语法约束在所有流程文档中一致。
- [ ] 义务覆盖判定不依赖单一样例流程，且可回溯到标准文档。
- [ ] `process-inventory.md` 与 `shared/registry/process_registry.json` 一致。
- [ ] `delivery-iterations` 的质量门禁与 HOLD 路由复用路径可追溯。
- [ ] fail-closed 与升级链在流程文档中可执行。

## 5. 完成定义（DoD）

- [ ] 形成“P4 -> P6 -> 证据目录”追溯闭环。
- [ ] 至少 1 条双主线链路完成可回放 dry-run。
- [ ] 提交仅包含 process/business/inventory 与必要治理文档。

## 6. 提交前校验

1. `entire status --detailed`
2. `python3 /Users/albus/MyProjects/ANC_v2/skills/system/entire-codex-sync/scripts/entire_codex_bridge.py sync --prompt "..." --summary "..." --files ...`
3. `python3 /Users/albus/MyProjects/ANC_v2/shared/registry/registry_contract_tool.py verify`
4. `git log -1 --pretty=raw`（确认 `Entire-Checkpoint`）
