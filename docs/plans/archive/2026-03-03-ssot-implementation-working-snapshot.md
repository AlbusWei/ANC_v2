# SSOT Implementation — Superpower-Replacement + OpenJudge SDD/TDD Execution Plan

> Status: Active SSOT
> Last Updated: 2026-03-03
> Required Execution Skill: `superpowers:executing-plans`

## 1) 权威范围

本文件是该主题唯一实施真相（implementation SSOT）。

Supersedes:
- `docs/plans/archive/2026-02-27-m1-m3-gate-authenticity-implementation.md`
- `docs/plans/archive/2026-03-01-m4-m5-productized-lifecycle-implementation.md`
- `docs/plans/archive/2026-03-01-m4-m5-implementation-assets-plan.md`
- `docs/plans/archive/2026-03-01-m1-m3-m4-m5-executable-gap-closure-implementation.md`
- 所有依赖 OpenSpec 主链输入输出的历史实施结论

## 2) 总体执行策略

按 Batch 0 -> 4 线性推进，先改契约字段与流程，再替换技能执行入口，再完成 SDD/TDD 绑定与清理残留，最后统一回归与 SSOT 对账。

- Batch 0: 契约硬切（OpenSpec 字段移除）
- Batch 1: 技能替换（openspec-sync -> superpower-sync）
- Batch 2: SDD+TDD 绑定（superpower_ref 强制进入 gate）
- Batch 3: 主链残留清除（脚本/测试/校验器）
- Batch 4: 文档索引与 SSOT 收口验证

## 3) 执行任务（唯一有效任务集）

### Batch 0 — 契约硬切（流程与协议）

1. 修改 `processes/meta/construction-plane-governance/process.json`
   - `openspec_ref -> superpower_ref`
   - `openspec_sync_ref -> superpower_sync_ref`
   - p4 改为 `sync-superpower-state`
2. 修改 `processes/meta/construction-plane-governance/SKILL.md`
3. 修改 `processes/meta/construction-plane-governance/PROCESS.md`
4. 新增 `docs/design/interfaces/superpower-collaboration-protocol.md`
5. 新增 `docs/design/data-models/superpower-collaboration-schema.json`
6. 新增 `docs/design/processes/atomic/AP-035-superpower-round-sync.md`
7. 旧 openspec 协议相关文档标记 superseded 并从主链摘除引用

验证：
- `rg -n "openspec_ref|openspec_sync_ref" processes/meta/construction-plane-governance docs/design/interfaces docs/design/processes/atomic`
- 期望：主流程目标文件中无旧字段残留。

### Batch 1 — 技能替换（唯一执行入口）

1. 新增 `skills/system/superpower-sync/SKILL.md`
2. 新增 `skills/system/superpower-sync/TEST.md`
3. 新增 `skills/system/superpower-sync/scripts/superpower_sync.sh`
4. 更新 `processes/meta/construction-plane-governance/process.json` p4 `skill_id`
5. 更新 `shared/registry/skill_registry.json`（注册 superpower-sync，移除 openspec-sync 主链引用）
6. 主链仅保留 `skills/system/superpower-sync/*` 协同入口，不保留 legacy 占位

验证：
- `python3 shared/registry/registry_contract_tool.py verify`
- `rg -n "system.integration.superpower-sync" processes shared/registry docs/design/inventories`
- 期望：registry 校验通过；主链引用为 0。

### Batch 2 — SDD+TDD 硬绑定

1. 修改 `docs/design/modules/M1-openjudge-adapter-spec.md`
   - 输入契约加入 `superpower_ref` 必填
2. 修改 `docs/design/modules/M1-test-system.md`
   - 明确 `superpower_ref + TEST.md` 是 TDD 必需输入
3. 修改 `docs/design/skills/quality-gate-skills.md`
   - `evaluation-runner` 输入契约加入 `superpower_ref`
4. 修改 `docs/design/skills/self-development-skills.md`
   - SDD 输出契约补 `superpower_ref`
5. 修改 `docs/design/modules/M3-self-development.md`
   - 输入契约补 `superpower_ref` 必填
   - 输出契约补 `superpower_sync_ref` 与追溯约束
   - 验收矩阵去 OpenSpec 化（`M3-AC-05` 改为 superpower 会话工件校验）
6. 修改 `docs/design/modules/M4-lifecycle-management.md`
   - 切换为 `ProductVersionInstance` 治理语义
   - lifecycle-review 输入契约补 `superpower_ref`
7. 修改 `processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py`
   - 证据链校验加入 `superpower_ref` 可达性校验
8. 修改 `tests/m1-runtime/run_post_dev_regression.py`
   - 新增 `missing_superpower_ref -> fail-closed` 用例

验证：
- `python3 -m pytest tests/m1-runtime -q`
- `python3 tests/m1-runtime/run_post_dev_regression.py`
- 期望：缺 superpower_ref 场景 fail；其余链路保持可执行。

### Batch 3 — OpenSpec 主链残留清除

1. 修改 `shared/registry/registry_contract_tool.py`
   - 去掉 openspec 协同 schema 强制校验
   - 改为 superpower 协同 schema 强制校验
2. 修改 `tests/m6-governance/run_post_dev_regression.py`
3. 修改 `tests/m2-bpm-runtime/run_tc_full_dev_proc.py`
4. 修改 `skills/system/construction-audit/scripts/construction_audit.py`
5. 修改 `processes/meta/construction-plane-governance/scripts/run_round.py`
6. 修改 `processes/meta/construction-plane-governance/scripts/round_evidence_tool.py`

验证：
- `rg -n "openspec validate|openspec_ref|openspec_sync_ref" tests processes skills shared docs/design`
- 期望：主链目录不再依赖 openspec 主字段/主命令。

### Batch 4 — 索引与施工平面对账收口

1. 修改 `docs/design/inventories/process-inventory.md`
2. 修改 `docs/design/inventories/skill-inventory.md`
3. 修改 `docs/design/modules/module-dependency-matrix.md`
4. 修改 `docs/architecture/construction_plane.md`
5. 校验 `docs/plans/SSOT-design.md` 与本文件一致

验证：
- `python3 shared/registry/registry_contract_tool.py verify`
- `python3 tests/m6-governance/run_post_dev_regression.py`
- 全仓 grep 检查主链残留

## 4) DoD（完成定义）

1. 主流程字段中无 `openspec_ref/openspec_sync_ref`。
2. `system.integration.superpower-sync` 成为唯一施工协同同步技能入口。
3. M1 门禁对缺 `superpower_ref` 明确 fail-closed。
4. SDD 输出与 TDD 输入通过 `superpower_ref` 形成可追溯闭环。
5. registry 与关键回归套件通过。
6. SSOT、inventory、construction plane 同步完成且无漂移。

## 5) 执行纪律

1. 严格 TDD：先失败测试，再最小实现，再回归。
2. 每个 batch 完成后执行代码审查。
3. 不做兼容层，不保留双轨入口。
4. 不引入与本目标无关的重构。

## 6) 实施状态追踪

- Batch 0: completed
- Batch 1: completed
- Batch 2: completed
- Batch 3: completed
- Batch 4: completed

## 7) 变更日志

- 2026-03-01：完成 Batch 0/3/4 收口：
  - 旧 OpenSpec 协议/AP 文档改为 superseded（仅历史追溯，不再作为主链入口）。
  - `construction-plane-governance` 设计文档与 runtime contract baseline 全量切换到 `superpower_ref/superpower_sync_ref`。
  - `construction-audit` 的 SKILL/TEST 口径统一为 Superpower。
  - `construction-plane-skills.md`、`system-skills.md`、`agent-inventory.md` 同步到 `system.integration.superpower-sync`。
  - `m6-runtime-contract-examples.json` 样例字段与 round_id 命名切换为 superpower 语义。
  - `construction_plane.md` 对历史 OpenSpec 记录补充“仅历史追溯，现行主链以 Superpower 为准”声明。
- 2026-03-01：重写为“Superpower 完全替代 OpenSpec + OpenJudge 驱动 SDD/TDD”的执行基线。
- 2026-03-03：新增 M5 Hook 生命周期事件专项实施计划（Batch 5~10），并补充 OpenClaw 前置可执行性验证结论。

## 8) M5 Hook 生命周期事件实施计划（2026-03-03，待实施）

> 目标：把 `docs/plans/SSOT-design.md` 中 M5 的“双层 Hook + 自定义生命周期事件”设计转译为可执行计划。  
> 边界：本节仅定义实施批次、验证门禁与准入条件，不在本回合直接改造运行脚本。

### 8.1 前置验证（已执行）

已完成最小可执行性验证（本地 OpenClaw 2026.2.9）：

1. 工作区投影与最小校验通过：
   - `python3 tools/openclaw/switch_workspace.py --repo-root . --scope dev`
   - `openclaw config get agents.defaults.repoRoot --json`
   - `openclaw config get skills.load.extraDirs --json`
   - `openclaw skills info config-change-gatekeeper --json`
2. 网关与自动化运行面可达：
   - `openclaw health --json` 返回 `ok=true`
   - `openclaw cron status --json` 返回 `enabled=true`
   - `openclaw hooks list --json` / `openclaw hooks check --json` 可读
3. CLI 能力模型已核对：
   - Cron：`openclaw cron add --help` 支持 `--at|--every|--cron`、`--session main|isolated`、`--system-event|--message`、`--tz`、`--wake`
   - Heartbeat：`openclaw system heartbeat --help` 支持启停与 last 查询
   - Hook：`openclaw hooks install --help` 支持本地路径安装（可 `--link`）

验证结论：

1. 计划具备进入实施的运行前提。
2. 发现配置告警：`plugins.entries.matrix` 重复定义；当前不阻塞本计划，但需在实施前确认不会影响 Hook 加载路径解析。
3. 当前 CLI 帮助未显示 `--exact/--stagger` 参数，准点策略应按“固定时点表达式 + 实测偏移监控”设计，必要时通过 gateway/tool 调用补充 `schedule.staggerMs`。

### 8.2 实施约束（可执行性优先）

1. 领域事件优先：M5 不直接以平台内置事件做治理判定，平台事件仅做桥接输入。
2. 统一入口：平台层/领域层事件统一进入 `trigger-ingress-normalizer -> trigger-event-runtime`，禁止旁路。
3. Fail-Closed：缺 `evidence_ref`、`owner_agent_id`、`dedupe_key` 的领域事件不得进入提案链。
4. 无破坏接入：先增量接入 `m1/m3/m4/m5` 结束点事件产出，不重构主流程控制流。
5. 发布隔离：Hook 运行时集成资产默认放在 `runtime_data/private-assets/`，未完成标准化前不进入公开发布主链。

### 8.3 批次计划（Batch 5 -> 10）

#### Batch 5 — 领域事件契约与字典（Schema First）

任务：

1. 新增 `docs/design/interfaces/evolution-hook-event-protocol.md`。
2. 新增 `docs/design/data-models/evolution-hook-event-schema.json`。
3. 在 `docs/design/modules/M5-self-evolution.md` 与 `docs/design/processes/trigger-event-runtime-process.md` 增补引用与契约字段。
4. 增加事件字典（`m1.gate.*`、`m3.implementation.*`、`m4.lifecycle.*`、`m5.proposal.*`、`asset.health.*`）。

验证：

1. `python3 shared/registry/registry_contract_tool.py verify`
2. `rg -n "m1\\.gate|m3\\.implementation|m4\\.lifecycle|m5\\.proposal|asset\\.health" docs/design`

准入：

1. schema 可机读校验。
2. 字段与 `trigger-event-runtime` 输入契约闭合。

#### Batch 6 — 触发策略映射与去重口径固化

任务：

1. 新增 M5 事件匹配策略文档（事件名 -> 目标流程/动作）。
2. 固化去重口径：`event_id` 主键 + 回退键（`event_name + asset_ref + window_bucket + source_instance_id`）。
3. 固化升级策略：`gate.failed` 连续阈值、`hold` 超 SLA、`rollback.executed` 直接 critical。

验证：

1. `tests/m2-bpm-runtime` 新增或扩展用例：去重冲突/未命中策略/升级阈值。
2. `python3 tests/m2-bpm-runtime/run_tc_tg.py`

准入：

1. 未命中策略必须落盘 `unmatched_event_receipt`，无静默丢弃。

#### Batch 7 — Runner 结束点领域事件产出适配

任务：

1. 在以下 runner 的阶段结束点产出领域事件包：
   - `quality-gate-evaluation` -> `m1.gate.*`
   - `full-development`（或实施流程）-> `m3.implementation.*`
   - `lifecycle-review` -> `m4.lifecycle.*`
   - `owner-evolution-governance` -> `m5.proposal.*`
2. 统一调用事件封装器，确保 `event_id/evidence_ref/owner_agent_id/dedupe_key` 完整。
3. 事件包写入 `runtime_data/evolution/events/` 并同步触发 `trigger-event-runtime`。

验证：

1. `python3 -m pytest tests/m5-self-evolution -q`
2. `python3 tests/m2-bpm-runtime/run_tc_tg.py`

准入：

1. 四类流程至少各有 1 条真实事件回执可追溯。

#### Batch 8 — OpenClaw Hook 集成（平台桥接层）

任务：

1. 新增 Hook 集成包（建议放在 `runtime_data/private-assets/hooks/anc-lifecycle-events/`）。
2. 使用 `openclaw hooks install --link <hook-pack-path>` 安装并启用桥接 Hook。
3. 桥接 Hook 仅负责把平台事件转为标准 ingress 包，不做重计算。
4. 与 `tools/openclaw/switch_workspace.py` 对齐：定义切 workspace 后 Hook 可用性校验步骤。

验证：

1. `openclaw hooks list --json`
2. `openclaw hooks check --json`
3. Hook 触发日志存在且异常不外抛。

准入：

1. Hook 失败不影响其他 handler。
2. 桥接事件可稳定进入 `trigger-event-runtime`。

#### Batch 9 — Cron / Heartbeat 编排落地

任务：

1. Cron（isolated）落地 `improvement-review` 周期评审任务。
2. Cron（main + systemEvent）落地 owner 评审提醒与治理信号注入。
3. Heartbeat 落地 `asset-health-check` 常态巡检清单。
4. 固化时区策略：所有 cron 任务显式 `tz`。

验证：

1. `openclaw cron list --json`
2. `openclaw cron run <id> --expect-final`
3. `openclaw system heartbeat last`

准入：

1. 周期巡检与精确评审互不覆盖、互不冲突。
2. 失败任务有可追溯 run 记录与升级证据。

#### Batch 10 — 端到端准入回归（M5 专项）

任务：

1. 完成 `TC-M5-001~007` 对应可执行测试脚本与报告模板。
2. 新增 Hook 专项用例：
   - `TC-M5-HOOK-001` 领域事件 happy path
   - `TC-M5-HOOK-002` 缺 evidence fail-closed
   - `TC-M5-HOOK-003` 去重冲突 fail-closed
   - `TC-M5-HOOK-004` unmatched_event_receipt 必达
3. 汇总 `M5 -> M3 -> M1 -> M4` 主链与异常链路验收报告。

验证：

1. `python3 -m pytest tests/m5-self-evolution tests/m2-bpm-runtime -q`
2. `python3 shared/registry/registry_contract_tool.py verify`
3. `python3 tools/release/release_isolation_gate.py`

准入：

1. 主链路与异常链路都可复现。
2. `review -> active` 附加门禁（观测窗口 + 回滚演练）有证据可审计。

### 8.4 里程碑与交付物

1. Milestone A（Batch 5-6）：完成领域事件契约与策略，不改运行逻辑。
2. Milestone B（Batch 7-8）：完成事件产出与 Hook 桥接，可触发但未放量。
3. Milestone C（Batch 9-10）：完成 cron/heartbeat 编排与端到端准入回归。

交付物目录（目标）：

1. `docs/design/interfaces/evolution-hook-event-protocol.md`
2. `docs/design/data-models/evolution-hook-event-schema.json`
3. `runtime_data/evolution/events/`（运行证据）
4. `runtime_data/execution/evidence/m5-self-evolution/`（回归证据）

### 8.5 风险与回滚

1. 风险：Hook 噪声过高导致事件风暴。
   - 缓解：Batch 6 先做去重与阈值策略，Batch 8 默认灰度开启。
2. 风险：CLI 与文档参数差异（如准点调度参数）。
   - 缓解：以本地 CLI 可用参数为准，超出能力通过 gateway/tool 能力补齐并先验证。
3. 风险：跨 workspace 配置漂移。
   - 缓解：每次验证前强制执行 `switch_workspace.py` + 三条最小校验命令。

回滚策略：

1. Hook 集成按 entry 级别可禁用（不删除流程资产）。
2. Cron 任务按 job id 可 disable/rm。
3. Runner 事件产出适配通过特性开关回退到“仅落盘不分发”模式。

## 9) 实施状态追踪（M5 Hook 专项）

- Batch 5: pending
- Batch 6: pending
- Batch 7: pending
- Batch 8: pending
- Batch 9: pending
- Batch 10: pending
