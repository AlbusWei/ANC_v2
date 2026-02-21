# Trigger Governance Review Checklist (Template)

> 版本: v0.1.0 | 用途: 评审 `trigger-governance-test-proposal.md` 的执行充分性与治理一致性

## 1. Review Metadata

| 字段 | 填写 |
|---|---|
| Review Round |  |
| Date |  |
| Reviewer(s) |  |
| Branch |  |
| Scope |  |
| Related Proposal | `../review-layers-modules/docs/design/modules/trigger-governance-test-proposal.md` |

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

- [ ] `P1~P3` 为 Governance Module，`P4~P6` 为 Executable Flow。
- [ ] 触发规则独立为 `trigger_registry`（不并入 `process_registry`）。
- [ ] M2 负责触发运行时，M4 负责触发策略治理。
- [ ] 升级链固定为 `actor -> owner -> bpm -> admin -> human`。
- [ ] 去重策略为混合去重（`event_id` 优先，缺失回退业务语义键）。
- [ ] 漏跑策略为补跑优先（窗口内补跑，超窗升级 owner）。
- [ ] App/owner 不得直达 admin，系统写操作由 admin 执行。

## 5. Scenario A Review (Schedule: 3-min Report)

- [ ] `trigger_type=schedule` 与 `*/3 * * * *` 表达明确。
- [ ] `delivery_policy=exception-only` 已定义（无异常仅记账）。
- [ ] 执行链路包含 `bpm -> admin -> human`。
- [ ] TG-SCH-001 具备输入、预期行为、证据锚点。
- [ ] TG-SCH-002 具备输入、预期行为、证据锚点。
- [ ] TG-SCH-003 覆盖 owner override 留痕。
- [ ] TG-SCH-004 覆盖 `catchup_window` 补跑规则。

## 6. Scenario B Review (Event: Skill review->active)

- [ ] 事件过滤条件固定为 `entity_type=skill && review->active`。
- [ ] canonical event 最小字段完整。
- [ ] 执行链路包含 `trigger matcher -> bpm -> system-analyst`。
- [ ] TG-EVT-001 具备输入、预期行为、证据锚点。
- [ ] TG-EVT-002 覆盖去重拒绝与留痕。
- [ ] TG-EVT-003 覆盖证据缺失 Fail-Closed 与补数动作。

## 7. Security & Governance Review

- [ ] BPM 无系统高权限写能力（仅门禁与编排）。
- [ ] 高风险动作需 checkpoint 与回滚要求。
- [ ] override、补跑、去重拒绝均有独立证据条目。
- [ ] 风险不可判定时按高风险升级 admin。
- [ ] 触发事件与流程实例可双向追溯（`trigger_id` <-> `instance_id`）。

## 8. Consistency Review (Layers & Modules)

- [ ] `../review-layers-modules/docs/design/layers/L2-orchestration-governance.md` 与提案一致。
- [ ] `../review-layers-modules/docs/design/layers/L4-self-evolution.md` 的 analyst 分工无冲突。
- [ ] `../review-layers-modules/docs/design/layers/layer-interface-contracts.md` 的 Trigger/Hook 契约一致。
- [ ] `../review-layers-modules/docs/design/modules/M2-bpm-engine.md` 与 M2 运行时边界一致。
- [ ] `../review-layers-modules/docs/design/modules/M4-lifecycle-management.md` 与 M4 策略边界一致。
- [ ] `../review-layers-modules/docs/design/modules/module-dependency-matrix.md` 的触发治理路径说明一致。

## 9. Evidence Matrix (Fill-In)

| Item ID | Expected Evidence | Evidence Path | Result (PASS/FAIL/BLOCKED/N/A) | Notes |
|---|---|---|---|---|
| TG-SCH-001 | trigger log + instance + admin forward |  |  |  |
| TG-SCH-002 | trigger ledger heartbeat |  |  |  |
| TG-SCH-003 | override decision record |  |  |  |
| TG-SCH-004 | catchup run record |  |  |  |
| TG-EVT-001 | event + instance record |  |  |  |
| TG-EVT-002 | dedupe reject log |  |  |  |
| TG-EVT-003 | fail-closed + backfill request |  |  |  |

## 10. Findings Register (Fill-In)

| Finding ID | Severity (P0-P3) | Description | Owner | Status |
|---|---|---|---|---|
|  |  |  |  |  |

## 11. Definition of Done

- [ ] Checklist 全项完成评审或明确标注 N/A。
- [ ] 所有 FAIL/BLOCKED 条目进入 Findings Register 并指定 Owner。
- [ ] 形成一页“差异关闭计划”并附路径引用。
- [ ] 本轮结论通过 Entire sync 落盘。
