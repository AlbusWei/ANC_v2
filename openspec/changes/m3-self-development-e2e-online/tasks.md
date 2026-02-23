## 1. Session1（审计 + OpenSpec/M6 基座）

- [x] 1.1 完成 Entire/OpenClaw 基线命令执行：`entire status --detailed`、`entire_codex_bridge.py start`、`switch_workspace.py --repo-root .`、`openclaw config get ...`。
- [x] 1.2 创建 change `m3-self-development-e2e-online` 并落盘 `proposal.md`、`design.md`、`tasks.md`、`thread-plan.md`、`m3-gap-baseline.md`。
- [x] 1.3 新增 `specs/m3-self-development-e2e-online-foundation/spec.md` 与 `specs/construction-plane/spec.md`，包含 Requirement + Scenario。
- [x] 1.4 初始化 M6 证据目录并写入 `round_open`。
- [x] 1.5 更新 `docs/architecture/construction_plane.md`，明确 Session2~Session7 依赖与 DoD。

## 2. Session2（设计闭合收敛，仅文档）

- [x] 2.1 新增 `registry-sync-process` 与 `escalation-process` 设计文档，补齐输入/输出/Fail-Closed/test_mount/lifecycle。
- [x] 2.2 更新 `full-development/hotfix/refactor` 三流程文档，补齐 `process_type` 与 `governance_bundle` 治理绑定蓝图。
- [x] 2.3 补齐 `sys.arch.impact-analyzer`、`sys.admin.release-manager` 定义卡并同步 `self-development-skills`。
- [x] 2.4 重写 `release-manager-agent` 为可运行资产口径设计（handoff 输入/成功输出/拒绝输出）。
- [x] 2.5 更新 inventories + `construction_plane.md` + OpenSpec 文档（`design/tasks/m3-gap-baseline`）联动闭合。
- [x] 2.6 执行门禁并归档结果：`openspec validate`、`registry verify`、契约关键字检索已通过。

## 3. Session3（缺失资产最小可执行落地）

- [x] 3.1 落地 `skills/system/impact-analyzer/` 与 `skills/system/release-manager/`（含 `SKILL.md/TEST.md` 与最小 runner）。
- [x] 3.2 落地 `processes/meta/registry-sync/` 与 `processes/meta/escalation/`（含 `process.json`、执行入口、最小测试挂载）。
- [x] 3.3 落地 `agents/app/delivery/release-manager-agent/` 运行资产目录。
- [x] 3.4 更新 `shared/registry/{skill_registry.json,process_registry.json,agent_directory.json}`。
- [x] 3.5 完成 AP 包装流程全量落地并改造 `full-development/hotfix/refactor` 三主流程 manifest（phase 不再直连 skill，补齐 `process_type/governance_bundle`）。
- [x] 3.6 再次联动更新 `docs/design/*inventory*`、`docs/architecture/construction_plane.md` 与 OpenSpec 状态文档。

## 4. Session4（M3 专项运行级测试基座）

- [x] 4.1 新建 `tests/m3-self-development/TEST.md` 与 `tests/m3-self-development/live_cases.md`，固化 Session4 四类覆盖与 Session5/6 预留 case 规则。
- [x] 4.2 新建 `tests/m3-self-development/run_tc_online.py` 单 runner（`--suite/--case` 统一入口）。
- [x] 4.3 复用 `tests/m3-runtime/run_skill_contract_validation.py` 与 `tests/m1-runtime/run_post_dev_regression.py`，完成主链路/异常链路/Fail-Closed/回退返工四类断言并产出 evidence 索引。

## 5. Session5（内部主线 E2E）

- [ ] 5.1 基于 M3 canonical 流程执行内部主线 E2E。
- [ ] 5.2 形成关键异常可回退证据。
- [ ] 5.3 复核 `M3 -> M1 -> M4` 门禁链路无旁路。

## 6. Session6（外部主线 E2E）

- [ ] 6.1 复用同一 M3 能力执行外部主线 E2E。
- [ ] 6.2 验证外部主线不绕过 canonical 流程。
- [ ] 6.3 输出内外主线复用对照结论。

## 7. Session7（全链路收口到 review）

- [ ] 7.1 执行 OpenSpec + registry + construction plane + evidence 四向对账。
- [ ] 7.2 完成 `entire_codex_bridge.py sync` + 单提交 + trailer 校验。
- [ ] 7.3 生命周期仅收敛至 `review`（禁止推进 `active`）。
- [ ] 7.4 结束 bridge：`entire_codex_bridge.py end`。
