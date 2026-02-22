## 1. Session1（审计 + OpenSpec/M6 基座）

- [x] 1.1 完成 Entire/OpenClaw 基线命令执行：`entire status --detailed`、`entire_codex_bridge.py start`、`switch_workspace.py --repo-root .`、`openclaw config get ...`。
- [x] 1.2 创建 change `m3-self-development-e2e-online` 并落盘 `proposal.md`、`design.md`、`tasks.md`、`thread-plan.md`、`m3-gap-baseline.md`。
- [x] 1.3 新增 `specs/m3-self-development-e2e-online-foundation/spec.md` 与 `specs/construction-plane/spec.md`，包含 Requirement + Scenario。
- [x] 1.4 初始化 M6 证据目录 `docs/design/modules/evidence/construction-plane/R-20260222-M6-m3-self-development-e2e-online-01/` 并写入 `round_open`。
- [x] 1.5 更新 `docs/architecture/construction_plane.md`，明确 Session2~Session7 依赖与 DoD（非泛化）。

## 2. Session2（设计闭合收敛）

- [ ] 2.1 输出 manifest 与 `development-loop-core-standard` 差距闭合报告，并更新 `m3-gap-baseline.md` 状态列。
- [ ] 2.2 校验 `m3-gap-baseline.md` 与 `design/tasks/specs` 的一致性并记录审计结果。
- [ ] 2.3 执行 `openspec validate m3-self-development-e2e-online --json`，作为 Session2 关闭门禁。

## 3. Session3（缺失资产最小可执行落地）

- [ ] 3.1 落地 `sys.arch.impact-analyzer` 与 `sys.admin.release-manager` 最小可执行资产（含设计文档与 test_mount）。
- [ ] 3.2 落地 `registry-sync`（process）与 `escalation`（process）最小可执行资产。
- [ ] 3.3 落地 `release-manager-agent` 运行资产。
- [ ] 3.4 完成联动更新：`docs/design/{skills,processes,agents}` + inventories + registries + construction plane。

## 4. Session4（M3 专项运行级测试基座）

- [ ] 4.1 新建 M3 测试目录与 `TEST.md`。
- [ ] 4.2 提供至少一个可执行 runner 入口（online smoke）。
- [ ] 4.3 覆盖 Fail-Closed 与回退路径用例，并输出可追溯证据索引。

## 5. Session5（内部主线 E2E）

- [ ] 5.1 基于 M3 canonical 流程执行内部主线 E2E。
- [ ] 5.2 形成完整证据目录并验证关键异常可回退。
- [ ] 5.3 复核门禁链路 `M3 -> M1 -> M4` 在内部主线无旁路。

## 6. Session6（外部主线 E2E）

- [ ] 6.1 基于同一 M3 能力执行外部主线 E2E。
- [ ] 6.2 验证外部主线未绕过 canonical 流程。
- [ ] 6.3 输出外部主线证据并与内部主线形成对照。

## 7. Session7（全链路收口到 review）

- [ ] 7.1 执行 OpenSpec + registry + construction plane + evidence 四向对账。
- [ ] 7.2 完成 `entire_codex_bridge.py sync` + 单提交 + trailer 校验。
- [ ] 7.3 将相关资产生命周期收敛至 `review`（禁止推进 `active`）。
- [ ] 7.4 结束 bridge 会话：`entire_codex_bridge.py end`。
