# Trigger Governance Review Checklist (Round 1)

> 版本: v0.2.0 | 用途: 评审 `trigger-governance-test-proposal.md` 的执行充分性与治理一致性

## 1. Review Metadata

| 字段 | 填写 |
|---|---|
| Review Round | Round 1 (Doc Review + Minimal Dry-Run) |
| Date | 2026-02-21 |
| Reviewer(s) | Codex |
| Branch | `codex/review-layers-modules` |
| Scope | 触发治理文档一致性评审 + `TG-SCH-002` / `TG-EVT-003` 最小 dry-run |
| Related Proposal | `docs/design/modules/trigger-governance-test-proposal.md` |

## 2. Review Objective

1. 验证触发治理方案满足“系统优先自维持 + 治理可审计 + Fail-Closed”。
2. 验证 M2/M4 边界与层间接口契约一致。
3. 验证两条 PoC 测试用例设计完整并可落证据。

## 3. Entire Session Discipline

1. `entire status --detailed`
2. `.../entire_codex_bridge.py start`
3. 文档改动后执行 `sync`
4. commit 后检查 `Entire-Checkpoint`
5. `.../entire_codex_bridge.py end`

## 4. Decision Baseline Lock

- [x] `P1~P3` 为 Governance Module，`P4~P6` 为 Executable Flow。
- [x] 触发规则独立为 `trigger_registry`（不并入 `process_registry`）。
- [x] M2 负责触发运行时，M4 负责触发策略治理。
- [x] 升级链固定为 `actor -> owner -> bpm -> admin -> human`。
- [x] 去重策略为混合去重（`event_id` 优先，缺失回退业务语义键）。
- [x] 漏跑策略为补跑优先（窗口内补跑，超窗升级 owner）。
- [x] App/owner 不得直达 admin，系统写操作由 admin 执行。

## 5. Scenario A Review (Schedule: 3-min Report)

- [x] `trigger_type=schedule` 与 `*/3 * * * *` 表达明确。
- [x] `delivery_policy=exception-only` 已定义（无异常仅记账）。
- [x] 执行链路包含 `bpm -> admin -> human`。
- [x] TG-SCH-001 具备输入、预期行为、证据锚点。
- [x] TG-SCH-002 具备输入、预期行为、证据锚点。
- [x] TG-SCH-003 覆盖 owner override 留痕。
- [x] TG-SCH-004 覆盖动态 `catchup_policy_ref` 补跑规则。

## 6. Scenario B Review (Event: Skill review->active)

- [x] 事件过滤条件固定为 `entity_type=skill && review->active`。
- [x] canonical event 最小字段完整。
- [x] 执行链路包含 `trigger matcher -> bpm -> system-analyst`。
- [x] TG-EVT-001 具备输入、预期行为、证据锚点。
- [x] TG-EVT-002 覆盖去重拒绝与留痕。
- [x] TG-EVT-003 覆盖证据缺失 Fail-Closed 与补数动作。

## 7. Security & Governance Review

- [x] BPM 无系统高权限写能力（仅门禁与编排）。
- [x] 高风险动作需 checkpoint 与回滚要求。
- [x] override、补跑、去重拒绝均有独立证据条目。
- [x] 风险不可判定时按高风险升级 admin。
- [x] 触发事件与流程实例可双向追溯（`trigger_id` <-> `instance_id`）。

## 8. Consistency Review (Layers & Modules)

- [x] `docs/design/layers/L2-orchestration-governance.md` 与提案一致。
- [x] `docs/design/layers/L4-self-evolution.md` 的 analyst 分工无冲突。
- [x] `docs/design/layers/layer-interface-contracts.md` 的 Trigger/Hook 契约一致。
- [x] `docs/design/modules/M2-bpm-engine.md` 与 M2 运行时边界一致。
- [x] `docs/design/modules/M4-lifecycle-management.md` 与 M4 策略边界一致。
- [x] `docs/design/modules/module-dependency-matrix.md` 的触发治理路径说明一致。

## 9. Evidence Matrix (Fill-In)

| Item ID | Expected Evidence | Evidence Path | Result (PASS/FAIL/BLOCKED/N/A) | Notes |
|---|---|---|---|---|
| TG-SCH-001 | trigger log + instance + admin forward | N/A（本轮未执行） | N/A | 仅完成提案级审查；执行留到下一轮 |
| TG-SCH-002 | trigger ledger heartbeat | `docs/design/modules/evidence/trigger-governance/TG-SCH-002-dry-run.md` | PASS | 文档级 dry-run，覆盖无异常仅记账 |
| TG-SCH-003 | override decision record | N/A（本轮未执行） | N/A | 仅完成提案级审查；执行留到下一轮 |
| TG-SCH-004 | catchup run record | N/A（本轮未执行） | N/A | 仅完成提案级审查；执行留到下一轮 |
| TG-EVT-001 | event + instance record | N/A（本轮未执行） | N/A | 仅完成提案级审查；执行留到下一轮 |
| TG-EVT-002 | dedupe reject log | N/A（本轮未执行） | N/A | 仅完成提案级审查；执行留到下一轮 |
| TG-EVT-003 | fail-closed + backfill request | `docs/design/modules/evidence/trigger-governance/TG-EVT-003-dry-run.md` | PASS | 文档级 dry-run，覆盖缺证据 Fail-Closed |

## 10. Findings Register (Fill-In)

| Finding ID | Severity (P0-P3) | Description | Owner | Status |
|---|---|---|---|---|
| FG-001 | P2 | 运行级证据尚未覆盖 TG-SCH-001/003/004 与 TG-EVT-001/002，需要在 trigger runtime 资产落地后补跑。 | bpm + qa | Open |

## 11. Definition of Done

- [x] Checklist 全项完成评审或明确标注 N/A。
- [x] 所有 FAIL/BLOCKED 条目进入 Findings Register 并指定 Owner。
- [x] 形成一页“差异关闭计划”并附路径引用：`docs/design/modules/trigger-governance-diff-closure-plan.md`
- [x] 本轮结论通过 Entire sync 落盘。
