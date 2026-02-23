## Context

`m3-self-development-e2e-online` 已完成 Session1 基座，本回合进入 Session2，目标是完成“设计层闭合”，不落运行目录，不推进生命周期到 `review/active`。

本回合强约束：

1. 只做设计资产与联动文档闭合，不做运行实现。
2. `registry-sync` 保持 P6/AP-011 原子语义。
3. `escalation` 采用 P5 可复用治理子流程语义。
4. `m3-gap-baseline` 采用“设计闭合/实现待落地”双状态拆分。

## Goals / Non-Goals

**Goals**

1. 将 M3 模块、三主流程、self-development 技能包、process/skill/agent 设计文档补到可直接实现。
2. 完成 design/inventory/construction-plane/OpenSpec 联动更新。
3. 形成可执行门禁：`openspec validate` + `registry verify` + 可检索契约字段。

**Non-Goals**

1. 不创建 `skills/system/*`、`processes/meta/*`、`agents/app/*` 运行目录。
2. 不新增 registry 实条目。
3. 不执行内部/外部主线 E2E。

## Decisions

### Decision A: `registry-sync` 保持原子流程口径

- 定位为 AP-011 的治理包装流程设计（P6）。
- 本回合仅新增 `docs/design/processes/registry-sync-process.md`。
- Session3 才落 `processes/meta/registry-sync/` 与 registry 条目。

### Decision B: `escalation` 采用 P5 可复用子流程

- 固定四段 phase：`incident-intake(AP-013)` -> `policy-check(AP-031 前置)` -> `chain-routing(AP-031)` -> `resolution-or-human(AP-025)`。
- 固定升级链：`actor -> owner -> bpm -> admin -> human`。

### Decision C: 三主流程先闭合治理绑定蓝图

- `full-development`: `process_type=dev.internal-productization`
- `hotfix`: `process_type=dev.hotfix`
- `refactor`: `process_type=dev.refactor`
- 三者统一补齐 `governance_bundle.{syntax_ref,obligation_ref,risk_policy_ref,checklist_ref}` 设计引用。

### Decision D: 生命周期目标统一为 `draft`

- Session2 新增/重写设计资产统一标注 `draft` 目标。
- 禁止在 Session2 声明任何 `review/active` 推进结论。

## Risks / Trade-offs

- [Risk] 设计文档闭合但实现资产未落地，可能被误解为“已经可运行”。
  - Mitigation: 在 gap 基线中拆分 `closed(design)` 与 `open(implementation)`。
- [Risk] `escalation` 作为 P5 与既有 P4 流程边界不清。
  - Mitigation: 固定 AP 映射与输入/输出契约，禁止越级替代业务流程。
- [Risk] 三主流程治理绑定只落文档，manifest 仍未更新。
  - Mitigation: Session3 明确将“目标态映射表 -> process.json 字段改造”作为首项实现任务。

## Migration Plan (Session-Level)

1. Session2：完成设计闭合（本回合）。
2. Session3：按 Session2 文档直接落运行资产目录 + registry 条目。
3. Session4：建立 M3 专项测试基座并覆盖 Fail-Closed/回退路径。
4. Session5/Session6：内部/外部主线 E2E。
5. Session7：四向对账并收敛到 `review`。

## Open Questions

已关闭：

1. `registry-sync` 与 `escalation` 资产粒度：已决策为“`registry-sync` 原子口径 + `escalation` P5 子流程”。

保留：

1. Session4 测试入口采用单 runner 还是分流程 runner（待 Session4 决策）。
2. Session7 `round_close` 是否在同回合执行或延后统一审计（待 Session7 决策）。

