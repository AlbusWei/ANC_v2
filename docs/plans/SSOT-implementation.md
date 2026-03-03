# Round Implementation Workspace（非长期SSOT）

> Status: Working Draft
> Last Updated: 2026-03-03
> Scope: 当前回合实施拆分与执行入口（回合结束后归档）

## 定位

本文件仅用于当前回合的实施拆分与执行节奏管理，不作为长期实施权威。

## 执行期查找规则（强制）

1. 本回合执行唯一入口：`docs/plans/SSOT-implementation.md`（当前文件）。
2. `docs/plans/archive/` 仅用于历史追溯，执行时不得作为主依据。
3. 仅在本回合关闭（全部 batch 结束）后，才将本文件快照归档并开启下一回合工作台。

长期实施依据：

1. `docs/architecture/`（机制与约束）
2. `docs/design/`（流程、接口、模型设计）
3. `docs/design/inventories/*.md` 与 `shared/registry/*.json`（资产清单与注册契约）
4. `docs/architecture/construction_plane.md`（阶段推进与准入状态）

## 当前回合实施入口（M5 Hook 专项）

1. Batch 5：领域事件协议与 schema 落盘。
2. Batch 6：事件匹配/去重/升级策略落盘。
3. Batch 7：runner 结束点领域事件产出适配。
4. Batch 8：OpenClaw Hook 平台桥接层集成。
5. Batch 9：Cron/Heartbeat 编排与验证。
6. Batch 10：端到端准入回归与 Fail-Closed 收口。

## 前置可执行性验证（已完成）

本轮已在本地 OpenClaw 2026.2.9 完成前置检查：

1. 工作区切换与配置投影通过：
   - `python3 tools/openclaw/switch_workspace.py --repo-root . --scope dev`
   - `openclaw config get agents.defaults.repoRoot --json`
   - `openclaw config get skills.load.extraDirs --json`
2. 运行面可达：
   - `openclaw health --json`（`ok=true`）
   - `openclaw cron status --json`（`enabled=true`）
   - `openclaw hooks list --json` / `openclaw hooks check --json`
3. 能力边界核验：
   - `openclaw cron add --help`（`--at|--every|--cron`、`--session`、`--system-event|--message`、`--tz`）
   - `openclaw system heartbeat --help`
   - `openclaw hooks install --help`

风险备注：

1. 存在配置告警：`plugins.entries.matrix` 重复定义。当前不阻塞，但在 Batch 8 前需复核 Hook 加载行为未受影响。

## 实施总目标（本回合）

1. 把 M5 的“平台桥接 + 领域事件主信号”触发架构落成可执行链路。
2. 打通 `domain event -> trigger-event-runtime -> AssetIssue/EvolutionProposal -> M3/M1/M4`。
3. 用回归用例证明主链可跑通、异常链可 Fail-Closed、证据链可审计。

## 批次实施计划（详细）

### Batch 5 — 协议与模型落盘（Schema First）

状态：`completed`（文档层完成，代码层无变更）

输入：

1. `docs/architecture/system_overview.md`
2. `docs/architecture/process_architecture.md`

产出（已完成）：

1. `docs/design/interfaces/evolution-hook-event-protocol.md`
2. `docs/design/data-models/evolution-hook-event-schema.json`
3. `docs/design/processes/owner-evolution-governance-process.md`
4. 相关索引同步（`governance-processes`、`meta-processes`、`process-inventory`）

验证：

1. `python3 -m json.tool docs/design/data-models/evolution-hook-event-schema.json`
2. `rg -n "owner-evolution-governance|evolution-hook-event" docs/design docs/architecture`

准入：

1. 协议、schema、流程设计三者字段口径一致。

### Batch 6 — 事件策略与去重规则实现

状态：`completed`（2026-03-03，代码与测试已落盘）

目标：

1. 将协议中的事件匹配、去重和升级规则落实到可执行策略文件。

实施项：

1. 新增策略资产：
   - `runtime_data/private-assets/evolution/event-routing-policy.json`
   - `runtime_data/private-assets/evolution/event-escalation-policy.json`
2. 在 `trigger-event-runtime` runner 增加策略读取与校验入口。
3. 实现未命中策略时 `unmatched_event_receipt` 强制落盘。

验证：

1. `python3 tests/m2-bpm-runtime/run_tc_tg.py`
2. `python3 -m pytest tests/m5-self-evolution/test_event_policy_runtime.py -q`
3. 新增用例：`TC-M5-HOOK-POLICY-001~003`（未命中、去重冲突、升级阈值）

准入：

1. 去重冲突不可判定必须 fail。
2. 未命中策略必须有回执，禁止静默丢弃。

### Batch 7 — Runner 结束点领域事件产出

状态：`completed`（2026-03-03，M1/M3/M4/M5 四类来源事件均已可追溯）

目标：

1. 在关键流程结束点稳定产出领域事件包并进入统一触发路径。

实施项：

1. 在以下 runner 增加 `emit_domain_event`：
   - `processes/meta/quality-gate-evaluation/scripts/quality_gate_evaluation_runner.py`
   - `processes/meta/full-development/scripts/full_development_runner.py`（以及 hotfix/refactor 对应 runner）
   - `processes/meta/lifecycle-review/scripts/lifecycle_review_runner.py`
2. 事件输出落盘到 `runtime_data/evolution/events/`。
3. 事件包字段严格按 `evolution-hook-event-schema.json` 生成。

验证：

1. `python3 -m pytest tests/m5-self-evolution -q`
2. `python3 tests/m2-bpm-runtime/run_tc_tg.py`
3. `python3 tests/m5-self-evolution/run_tc_online.py`

准入：

1. 至少四类来源事件（M1/M3/M4/M5）各有一条可追溯回执（已完成）。

### Batch 8 — OpenClaw Hook 平台桥接层集成

状态：`completed`（2026-03-03，Hook 包已安装并线上触发验证通过）

目标：

1. 接入平台层 Hook，把外部/会话信号桥接为标准 ingress 包。

实施项：

1. 新增 Hook 包目录：
   - `runtime_data/private-assets/hooks/anc-lifecycle-events/`
2. 安装与启用：
   - `openclaw hooks install --link runtime_data/private-assets/hooks/anc-lifecycle-events`
3. Hook 行为限制：
   - 仅桥接事件，不做重计算
   - 异常本地捕获，不外抛

验证：

1. `openclaw hooks list --json`
2. `openclaw hooks check --json`
3. 触发日志检查（含异常隔离）

准入：

1. Hook 故障不会连带影响其他 handler。
2. 桥接事件能进入 `trigger-event-runtime`。

### Batch 9 — Cron / Heartbeat 编排落地

状态：`completed`（2026-03-03，Cron/Heartbeat 已落地并完成线上运行审计）

目标：

1. 将常态巡检与精确动作在 OpenClaw 中落为可运行任务。

实施项：

1. Cron（isolated）创建 `improvement-review` 周期任务。
2. Cron（main + systemEvent）创建 owner 评审提醒任务。
3. Heartbeat 清单增加 `asset-health-check`。
4. 所有 cron 显式设置 `tz`。

验证：

1. `openclaw cron list --json`
2. `openclaw cron run <job-id> --expect-final`
3. `openclaw system heartbeat last`

准入：

1. Heartbeat 与 Cron 职责分离，无重复触发风暴。
2. 失败 run 能在历史记录中审计。

### Batch 10 — 端到端准入回归

状态：`completed`（2026-03-03，准入门禁全部通过）

目标：

1. 验证 M5 主链可运行，异常链可 Fail-Closed，且证据链完整。

实施项：

1. 完成并执行：
   - `TC-M5-001~007`（主链与基础异常链）
   - `TC-M5-HOOK-001~004`（领域事件专项）
2. 生成自然语言验收结论与风险判断。
3. 同步更新 `construction_plane` 对应条目状态。

验证：

1. `python3 -m pytest tests/m5-self-evolution tests/m2-bpm-runtime -q`
2. `python3 shared/registry/registry_contract_tool.py verify`
3. `python3 tools/release/release_isolation_gate.py`

准入：

1. 主链路与异常链路均可复现。
2. `review -> active` 附加门禁（观测窗口 + 回滚演练）证据齐备。

执行结果（2026-03-03）：

1. Batch 8 结果：
   - Hook 包：`runtime_data/private-assets/hooks/anc-lifecycle-events/`
   - 实装内容：`package.json` + `HOOK.md` + `handler.js`
   - 线上验证：`openclaw hooks list/check` 可见 `lifecycle-event-bridge`，`gateway restart` 后可产生 bridge ingress/dispatch 与 runtime output。
2. Batch 9 结果：
   - Cron 任务：`m5-improvement-review`（isolated）与 `m5-owner-review-reminder`（main + systemEvent）均已创建，`tz=Asia/Shanghai`。
   - Heartbeat 清单：`agents/app/entry/personal-assistant/HEARTBEAT.md` 增加 `asset-health-check`。
   - 审计验证：`openclaw cron run --expect-final` + `openclaw cron runs --id` + `openclaw system heartbeat last` 均可给出结构化结果。
3. Batch 10 结果：
   - 新增准入回归：`tests/m5-self-evolution/test_m5_admission_regression.py`（`TC-M5-001~007` + `TC-M5-HOOK-001~004`）。
   - 新增 Hook 包测试：`tests/m5-self-evolution/test_hook_bridge_pack.py`。
   - 线上套件：`tests/m5-self-evolution/run_tc_online.py`（`TC-M5-HOOK-ONLINE-001~007`）。
   - 门禁结论：`pytest`、`registry verify`、`release_isolation_gate` 全部通过。

## 里程碑节奏（建议）

1. Milestone A（1 个回合）：完成 Batch 6（策略可执行化）。
2. Milestone B（1-2 个回合）：完成 Batch 7-8（事件产出 + Hook桥接）。
3. Milestone C（1 个回合）：完成 Batch 9-10（编排 + 准入回归）。

## 失败回滚策略

1. Hook 回滚：按 entry 禁用或卸载，不回滚核心流程代码。
2. Cron 回滚：按 job id `disable/rm`。
3. 事件产出回滚：保留落盘、关闭分发开关，退回“只采集不触发”模式。
4. 准入失败：保持 `draft/review`，禁止推进 `active`。

## 当前状态追踪

1. Batch 5：completed
2. Batch 6：completed
3. Batch 7：completed
4. Batch 8：completed
5. Batch 9：completed
6. Batch 10：completed

## 归档规则

1. 本文件不保留历史批次明细；历史内容统一归档到 `docs/plans/archive/`。
2. 本轮快照：`docs/plans/archive/2026-03-03-ssot-implementation-working-snapshot.md`。
