# 流程协作骨架 v1（设计导向）修正计划

> 适用 change: `m3-meta-asset-quality-hardening`  
> 基准文档: `docs/architecture/process_architecture.md`  
> 试点流程: `quality-gate-evaluation`

## 1. 背景与目标

当前流程资产已具备“可描述的 phase 链”，但多处仍停留在本地脚本串行编排，尚未把“流程 = 多 Agent/多会话协作协议”作为运行内核落地。

本计划目标：

1. 先建立可执行的协作骨架，优先保证“能跑起来、能协作、能回放”。
2. 以 `quality-gate-evaluation` 作为首个试点，验证 BPM 分发与跨角色会话协作。
3. 在试点可运行后，再扩展到 `full-development/hotfix/refactor`。

## 2. 本回合已确认决策

1. AP 穿透策略：采用 **1B**。允许“同 Actor、低风险、临时旁路 AP”的直调，但必须标注 `ap_bypass_reason`，并限定在迁移窗口。
2. 会话粒度：采用 **2A**。每个 phase 使用隔离会话（isolated session），禁止把 phase 堆积进同一主会话。
3. 迭代策略：采用“先跑后补”。先把协作主链跑通，运行中暴露问题后再补强契约与规则。
4. 试点范围：先做 QA 主线试点，即 `quality-gate-evaluation`。
5. 表达策略：采用 **5A**。自然语言上下文为一等输入，结构化契约作为可选增强，不反客为主。

## 3. 协作骨架 v1（最小可运行）

### 3.1 phase 最小语义字段（先语义，后结构）

每个 phase 至少落盘以下信息：

1. `phase_purpose`：本阶段业务目的（自然语言）。
2. `actor`：本阶段执行角色。
3. `input_context_ref`：输入上下文包（Markdown/JSON 均可，优先自然语言描述）。
4. `done_definition`：判定“完成”的自然语言标准。
5. `handoff_note`：给下一阶段执行者的交接说明。

### 3.2 BPM 分发最小动作

1. 每个 phase 启动前由 BPM 创建独立实例上下文与独立 session。
2. BPM 以 `openclaw agent --session-id <phase-session-id>` 分发任务给 phase actor。
3. phase 完成后落盘自然语言完成摘要与输出引用，再进入下一 phase。

### 3.3 AP 迁移过渡规则（与 1B 一致）

1. 优先走 P6 AP。
2. 暂时无法走 AP 的 phase，可保留直调 skill，但必须显式记录：
   - `ap_bypass=true`
   - `ap_bypass_reason`
   - `planned_ap_id`
   - `planned_migration_round`

## 4. QA 试点改造范围

试点对象：`processes/meta/quality-gate-evaluation/`

改造目标：

1. 把 `p1~p5` 的执行过程从“纯本地脚本串行”升级为“BPM phase 分发 + 隔离会话”。
2. 保留当前可运行逻辑作为 fallback（避免一次性替换导致回归阻断）。
3. 产出可回放证据：phase 级会话映射、交接文本、完成摘要、输出引用。

## 5. 分阶段执行（P8）

### P8.1 语义骨架落盘

1. 更新试点流程设计文档，补全每个 phase 的目的、输入上下文、交接语义。
2. 更新 `process.json`，增加过渡字段（如 `ap_bypass_reason`）。

### P8.2 运行路径接线

1. 更新 `process-instance-manager`，让 phase 分发支持默认执行 OpenClaw 分发（可保留显式关闭开关）。
2. 在 `quality_gate_evaluation_runner.py` 中接入 phase 级 isolated session 分发。

### P8.3 运行验证

1. 先跑试点流程 happy path。
2. 再跑 hold 路由场景（`p4 -> p5`）。
3. 汇总“协作可运行性”结论，不以字段完备度作为主结论。

## 6. 完成判据（设计导向）

1. 能证明至少一条 QA 主链在多会话协作模式下可运行。
2. phase 之间的交接语义可被下一 actor 直接理解并继续执行。
3. 出现失败时能明确定位是“语义断裂”还是“实现缺陷”，并可快速迭代。
4. 不把“格式通过”当作完成，完成以“协作主目标跑通”为准。

## 7. 当前开放问题

1. AP 旁路的迁移窗口建议按回合计数还是按日期计时，需要在试点跑一轮后再定。
2. phase 级自然语言上下文包的模板是否需要统一（建议试点后再固化模板）。

## 8. 全量流程偏差地图（2026-02-23 横向扫描）

> 扫描范围：`processes/meta/*/process.json` + `docs/design/processes/*-process.md`

### 8.1 宗旨偏差（流程被“实现脚本化”，协作语义不足）

1. 20/20 个 `process.json` 的 phase 都缺少 `phase_purpose/input_context_ref/done_definition/handoff_note` 这类“协作语义字段”。
2. 13 份流程设计文档中，仅 1 份（`quality-gate-evaluation-process.md`）系统描述了 phase 输入上下文、完成标准、交接说明与会话分发。
3. 现状更接近“phase 调用清单”，离“多 Agent/多会话协作协议”仍有明显距离。

### 8.2 AP 映射偏差（P6 原子流程运行层未成形）

1. 当前 `processes/` 下尚无 AP 运行资产目录（仅有文档层 AP 定义）。
2. 20 个元流程中，16 个流程存在 `target_type=skill` 直调 phase（共 51 个 skill phase），AP 包装主要停留在文档语义层。
3. 按既定决策 `1B`，可在迁移窗口临时保留直调，但必须带迁移标记并有退出路径。

### 8.3 运行架构偏差（BPM 分发能力尚未普及）

1. 当前仅 `quality-gate-evaluation` runner 接入了 phase 级分发与 isolated session。
2. 其它主流程（`full-development/hotfix/refactor`）尚未接线 BPM phase 分发，仍以本地串行执行为主。
3. 因此“流程价值 = 协作编排”目前只在 QA 试点局部成立。

### 8.4 标准口径偏差（规范间存在冲突）

1. `docs/architecture/process_architecture.md` 的 canonical schema 允许 `target_type=skill`，但 `docs/design/processes/development-loop-core-standard.md` 明确“不允许 skill 作为 phase 直接执行单元”。
2. 运行层已需要 `hold/escalate/skip` 语义，而部分规范描述仍以二值完成态为主，造成设计与实现口径不一致。
3. 这会直接导致团队在“是否允许临时直调 skill”与“状态机应该如何表达”上频繁争论。

## 9. 修正计划（骨架优先，先跑后补）

### R1（已完成）QA 试点跑通

1. 在 `quality-gate-evaluation` 落地 phase 级 isolated session 分发骨架。
2. 验证 happy path 与 hold 路由均可在协作模式跑通。
3. 结论：协作主目标可运行，具备向主流程扩展的基础。

### R2（下一回合）主流程骨架扩展

1. 目标范围：`full-development`、`hotfix`、`refactor`。
2. 每个 phase 至少补齐：目的、输入上下文、完成定义、交接语义（自然语言优先）。
3. 运行层接线：为三条主流程补 phase-dispatch + isolated session（先证据链模式，后真实 openclaw 分发）。

### R2.1（已完成）full-development 首条主流程扩展

1. 真实分发策略：`full-development` 已切换为真实 openclaw phase 分发。
2. 会话隔离策略：同 actor 跨 phase 通过 `sessions.reset` 强制新会话。
3. 运行结果：`TC-FULL-DEV-PROC-001` 通过，`phase_count=8`，`actor_isolation_ok=true`。

### R3（后续回合）AP 迁移收敛

1. 对临时直调点建立迁移台账：`ap_bypass_reason/planned_ap_id/planned_migration_round`。
2. 迁移顺序按流程顺序推进，不做风险分层（用户决策）。
3. 当主流程协作稳定后，再逐步收紧契约门禁，避免先规范后瘫痪。

## 10. 当前建议讨论题（苏格拉底式）

1. 对你而言，“主流程协作跑通”的最小判据是“能跨角色接力并完成目标”，还是“必须含真实 openclaw 分发回执”？
2. 在 `full-development/hotfix/refactor` 三条主流程里，你希望先扩展哪一条，才能最快暴露我们骨架设计的核心缺陷？
3. 对 AP 迁移窗口，你更倾向“按流程回合收敛”还是“按风险等级分层收敛”（高风险先强制 AP，低风险后迁移）？

## 11. 讨论收敛（2026-02-23）

1. 最小判据已确认：必须含真实 openclaw 分发回执，不接受仅本地模拟分发。
2. 扩展顺序已确认：先做 `full-development`，再推进 `hotfix/refactor`。
3. AP 迁移已确认：按顺序推进，不做风险分层。
