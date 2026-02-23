# m3-self-development-e2e-online Session1~Session7 分拆执行总计划

## 元信息

- round_id: `R-20260222-M6-m3-self-development-e2e-online-01`
- openspec_ref: `m3-self-development-e2e-online`
- 本文角色: 本 change 会话编排唯一对齐源
- 本轮边界: Session3 运行资产全量落地已完成，当前进入 Session4+ 运行级扩展阶段

## 线程顺序

`Session1 -> Session2 -> Session3 -> Session4 -> Session5 -> Session6 -> Session7`

## Session 计划

### Session1（当前会话）

- 目标: 完成设计闭合差距审计与 OpenSpec/M6 基座初始化。
- 输入:
  - `AGENTS.md`
  - `docs/architecture/construction_plane.md`
  - `docs/design/modules/M3-self-development.md`
  - `docs/design/processes/development-loop-core-standard.md`
- 输出:
  - `openspec/changes/m3-self-development-e2e-online/{proposal.md,design.md,tasks.md,thread-plan.md,m3-gap-baseline.md}`
  - `openspec/changes/m3-self-development-e2e-online/specs/**/spec.md`
  - `docs/design/modules/evidence/construction-plane/R-20260222-M6-m3-self-development-e2e-online-01/{scope_baseline.md,open_questions.md,thread_handoff.md,round-evidence.jsonl}`
  - `docs/architecture/construction_plane.md`（Session2~Session7 DoD 专节）
- DoD:
  - `openspec validate m3-self-development-e2e-online --json` pass。
  - `m3-gap-baseline.md` 字段完整且每项映射到 Session2~Session6。
  - `round-evidence.jsonl` 首条为 `round_open`。

### Session2（设计闭合差距收敛）

- 输入: Session1 全量产出 + M3 三流程 manifest。
- 输出:
  - 差距状态更新后的 `m3-gap-baseline.md`
  - 必要的 design/specs 变更补丁
- 依赖: Session1 完成并提交。
- DoD:
  - `m3-gap-baseline.md` 与 `design/tasks/specs` 一致。
  - `openspec validate m3-self-development-e2e-online --json` pass。
  - 明确未闭合项的阻断级别与下一会话 owner。

### Session3（缺失资产落地）

- 输入: Session2 闭合清单。
- 输出:
  - 5 项缺失资产最小可执行落盘（skill/process/agent）
  - AP 包装流程族全量落地（7 个 bundle）与三主流程 manifest 改造闭合
  - `tests/m3-runtime/run_skill_contract_validation.py` 统一契约验证入口与 evidence 输出
  - 对应设计文档、inventories、registries、construction plane、OpenSpec 联动更新
- 依赖: Session2 完成并提交。
- DoD:
  - 缺失资产路径可达、契约可解析。
  - `python3 tests/m3-runtime/run_skill_contract_validation.py` pass。
  - `python3 shared/registry/registry_contract_tool.py verify` pass。
  - `openspec validate m3-self-development-e2e-online --json` 返回 `valid=true`。
  - 生命周期状态保持 `draft/review` 合规，不越级 `active`。

### Session4（M3 专项测试基座）

- 输入: Session3 资产。
- 输出:
  - 在 `tests/m3-runtime/` 扩展 M3 主链路/异常链路/回退路径 case 索引
  - Fail-Closed 与回退路径测试说明
- 依赖: Session3 完成并提交。
- DoD:
  - `tests/m3-runtime/run_skill_contract_validation.py` 持续可执行。
  - 失败路径与恢复/回退路径均有证据。

### Session5（内部主线 E2E）

- 输入: Session4 测试基座。
- 输出:
  - 内部主线 E2E 证据包
- 依赖: Session4 完成并提交。
- DoD:
  - 内部主线关键场景通过。
  - 异常链路可恢复/可回退并可审计。

### Session6（外部主线 E2E）

- 输入: Session5 内部主线结果。
- 输出:
  - 外部主线 E2E 证据包
  - 内外主线复用对照结论
- 依赖: Session5 完成并提交。
- DoD:
  - 外部主线复用 M3 canonical 流程且无旁路。
  - 外部主线关键场景通过并可追溯。

### Session7（全链路收口）

- 输入: Session1~Session6 全量证据与提交记录。
- 输出:
  - 对账结论与收口记录
  - 生命周期收敛记录（上限 review）
- 依赖: Session6 完成并提交。
- DoD:
  - OpenSpec + registry + construction plane + evidence 四向对账通过。
  - `git log -1 --pretty=raw` 含 `Entire-Checkpoint`。
  - `entire_codex_bridge.py end` 成功。

## 提交与同步纪律

1. 每个 Session 至少一次 `entire_codex_bridge.py sync`。
2. 每个 Session 至少一次独立提交。
3. 每次提交后必须检查 trailer。
4. 任一门禁失败即 Fail-Closed。
