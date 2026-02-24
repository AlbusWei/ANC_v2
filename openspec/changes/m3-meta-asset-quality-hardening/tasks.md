## 0. Phase0（初始化与规格一次落盘）

- [x] 0.1 执行初始化门禁：`entire status --detailed`、`entire_codex_bridge.py start`、`switch_workspace.py --repo-root .`、`openclaw config get ...`。
- [x] 0.2 新建独立 change：`m3-meta-asset-quality-hardening`（不混写 `m3-self-development-e2e-online`）。
- [x] 0.3 一次性落盘 `proposal/design/tasks/thread-plan/meta-gap-baseline`。
- [x] 0.4 一次性落盘 3 份 spec：`meta-asset-quality`、`process-architecture-refactor`、`qa-online-validation`。
- [x] 0.5 在旧 change `m3-self-development-e2e-online/tasks.md` 写入“Session5/6 前置依赖本 change 门禁通过”。
- [x] 0.6 执行 P0 校验命令并记录结论。

## 1. Phase1（方法论与迁移蓝图）

### 目标

建立流程拆分原则与 bundle 退役迁移矩阵，确保后续实现无歧义。

### 输入

1. `openspec/changes/m3-meta-asset-quality-hardening/{design.md,meta-gap-baseline.md}`
2. `docs/design/processes/*` 当前流程设计文档
3. `shared/registry/process_registry.json`

### 输出

1. `docs/design/standards/process-decomposition-methodology.md`
2. `docs/design/standards/process-definition-standard.md`（新增方法论章节）
3. `openspec/changes/m3-meta-asset-quality-hardening/meta-gap-baseline.md`（迁移矩阵）

### DoD / 门禁

1. `openspec validate m3-meta-asset-quality-hardening --json`
2. `rg -n "MECE|金字塔|单一职责|DIP|LoD|组合" docs/design/standards docs/design/processes`
3. `rg -n "ap-[0-9].*-bundle" openspec/changes/m3-meta-asset-quality-hardening/meta-gap-baseline.md`

## 2. Phase2（流程资产重构：bundle -> P5 子流程）

### 目标

移除 `ap-*-bundle` 运行依赖，完成主流程到 P5 子流程库的替换。

### 输入

1. Phase1 迁移矩阵
2. `processes/meta/{development-process,full-development,hotfix,refactor}`

### 输出

1. 新增 P5 子流程资产目录（含 `SKILL.md/PROCESS.md/process.json/scripts/TEST.md`）
2. 主流程 manifest 与 guide 文档更新
3. registry 流程条目更新

### DoD / 门禁

1. `python3 shared/registry/registry_contract_tool.py verify`
2. `rg -n "ap-[0-9].*-bundle" processes/meta shared/registry docs/design/processes`
3. `openspec validate m3-meta-asset-quality-hardening --json`

## 3. Phase3（Meta 技能全量升级）

### 目标

升级 8 个 Meta 技能并解决本地 `skill-creator` 同名冲突。

### 输入

1. `skills/meta/*`、`skills/skill-creator/*`
2. `shared/registry/skill_registry.json`
3. openclaw skill 可见性现状

### 输出

1. Meta 技能文档/runner/references/test 升级
2. 本地 `meta.arch.skill-creator` 运行名唯一化与兼容映射说明
3. skill registry 联动更新

### DoD / 门禁

1. `python3 shared/registry/registry_contract_tool.py verify`
2. `openclaw skills info agent-creator --json`
3. `openclaw skills info process-creator --json`
4. `openclaw skills info template-validator --json`
5. `openclaw skills info meta-skill-creator --json`
6. `rg -n "TODO" skills/skill-creator/scripts/scaffold_skill.py`

## 4. Phase4（联动闭合）

### 目标

完成 design/inventory/registry/construction-plane/OpenSpec 的一致性闭合，并明确本回合只做 Phase4，不进入 Phase5。

### 输入

1. Phase2/Phase3 改造结果
2. 现有设计与清单文档

### 输出

1. `docs/design/skills/*`、`docs/design/processes/*`、`docs/design/inventories/*` 更新
2. `shared/registry/{process_registry.json,skill_registry.json}` 更新
3. `docs/architecture/construction_plane.md` 更新
4. OpenSpec 文档状态回写
5. `shared/registry/skill_registry.json` 联动核对（允许 no-delta，但必须记录）

### 执行子项（决策版）

- [x] 4.1 联动清单已核对：`docs/design/{skills,processes,agents,inventories}`、`shared/registry/*`、`docs/architecture/construction_plane.md`、OpenSpec 变更文档。
- [x] 4.2 生命周期收敛（变更全覆盖）：11 个流程统一推进到 `review`，不推进 `active`。
- [x] 4.3 版本对齐（本 change 范围）：`process_registry.version == process.json.version == SKILL frontmatter.version`。
- [x] 4.4 M3 模块/依赖矩阵/Agent/Skill 文档联动更新，运行入口统一为 `meta-skill-creator`（`skill-creator` 仅历史别名）。
- [x] 4.5 `skill_registry` 联动复核完成：字段无增量（no-delta）。
- [x] 4.6 Fail-Closed 声明：任一门禁失败即判定 Phase4 未完成，禁止进入 Phase5。

### DoD / 门禁

1. `python3 shared/registry/registry_contract_tool.py verify`
2. `openspec validate m3-meta-asset-quality-hardening --json`
3. `rg -n "ap-[0-9].*-bundle" docs/design shared/registry openspec/changes/m3-meta-asset-quality-hardening`
4. version 对齐自检（11 流程三方一致）
5. 倒挂双向自检（`doc_claim_not_in_registry` 与 `registry_state_not_in_docs` 为空）

## 5. Phase5（QA 在线测试基座强化）

### 目标

建立 Meta 资产专项 QA 在线测试入口与证据结构。

### 输入

1. Phase2/3/4 资产
2. 现有 `tests/m3-self-development` 基座

### 输出

1. 在线套件设计与执行脚本
2. 用例矩阵（Happy/Fail-Closed/Traceability/Rollback）
3. 证据目录索引

### DoD / 门禁

1. `python3 tests/m3-self-development/run_meta_qa_online.py --list-cases`
2. `python3 tests/m3-self-development/run_meta_qa_online.py --dry-run`
3. `openspec validate m3-meta-asset-quality-hardening --json`

## 6. Phase6（QA 在线执行与缺陷闭环）

### 目标

执行在线套件并完成缺陷修复与回归通过。

### 输入

1. Phase5 在线测试基座
2. openclaw runtime 可执行环境

### 输出

1. 在线执行报告
2. 缺陷清单与修复记录
3. 回归通过证据

### DoD / 门禁

1. `python3 tests/m3-self-development/run_meta_qa_online.py`
2. `python3 shared/registry/registry_contract_tool.py verify`
3. `openspec validate m3-meta-asset-quality-hardening --json`

### 执行结果（2026-02-23）

1. `python3 tests/m3-self-development/run_meta_qa_online.py`：
   - round-1：`112/111/1`（发现阻断缺陷 `DEF-PH6-001`）
   - 修复与回归后 final：`112/112/0`（pass）
2. 高风险 Fail-Closed 稳定性验证：
   - 关键 4 技能 + `construction-plane-governance` FC，连续 3 轮全部通过。
3. 门禁结果：
   - `python3 shared/registry/registry_contract_tool.py verify`：pass
   - `openspec validate m3-meta-asset-quality-hardening --json`：pass
4. 证据索引：
   - `docs/design/modules/evidence/self-development/runtime-validation-round-meta-assets/latest/phase6_execution_rounds.json`
   - `docs/design/modules/evidence/self-development/runtime-validation-round-meta-assets/latest/phase6_defect_closure.json`
   - `docs/design/modules/evidence/self-development/runtime-validation-round-meta-assets/latest/phase6_defect_closure.md`
   - `docs/design/modules/evidence/self-development/runtime-validation-round-meta-assets/latest/phase6_final_conclusion.md`

## 7. Phase7（收口与状态推进到 review）

### 目标

四向对账、状态收敛到 `review`、Entire 审计闭环。

### 输入

1. Phase0~Phase6 全部产出
2. Entire 会话与提交信息

### 输出

1. 对账报告与收口结论
2. 生命周期迁移记录（仅到 `review`）
3. 完整审计信息（含 `Entire-Checkpoint`）

### DoD / 门禁

1. `python3 shared/registry/registry_contract_tool.py verify`
2. `openspec validate m3-meta-asset-quality-hardening --json`
3. `python3 tests/m3-self-development/run_meta_qa_online.py --suite final-regression`
4. `git log -1 --pretty=raw`（包含 `Entire-Checkpoint`）
5. `python3 skills/system/entire-codex-sync/scripts/entire_codex_bridge.py end`

## 8. Phase8（流程协作骨架 v1 + QA 试点，新增）

### 目标

以 `quality-gate-evaluation` 为首个试点，验证“多 Agent/多会话协作”在 BPM 下可运行，优先跑通主目标而非先追求格式完备。

### 输入

1. `docs/architecture/process_architecture.md`
2. `openspec/changes/m3-meta-asset-quality-hardening/process-collaboration-skeleton-v1-plan.md`
3. `processes/meta/quality-gate-evaluation/{process.json,PROCESS.md,scripts/quality_gate_evaluation_runner.py}`
4. `skills/system/process-instance-manager/scripts/process_instance_runner.py`

### 输出

1. QA 试点流程的 phase 级协作骨架（目的、输入上下文、完成定义、交接语义）。
2. phase 级 isolated session 分发能力（每个 phase 独立会话）。
3. 运行级证据：至少一条 happy path + 一条 hold 路由路径。

### 子任务

- [x] 8.1 将 `process-collaboration-skeleton-v1-plan.md` 中的骨架字段映射到 QA 试点流程定义。
- [x] 8.2 调整 `process-instance-manager` 分发行为，支持 phase 级默认分发（保留可关闭开关）。
- [x] 8.3 在 `quality_gate_evaluation_runner.py` 接入 isolated session phase 分发。
- [x] 8.4 执行 QA 试点回归并输出自然语言可用性结论（主链 + hold 路由）。

### DoD / 门禁

1. `python3 tests/m2-bpm-runtime/run_tc_qa_proc.py`
2. `python3 shared/registry/registry_contract_tool.py verify`
3. `openspec validate m3-meta-asset-quality-hardening --json`
4. 试点结论必须包含“是否跑通多会话协作主目标”的自然语言结论，不得只贴日志。

### 执行结果（2026-02-23）

1. 验证命令：
   - `python3 tests/m2-bpm-runtime/run_tc_qa_proc.py`：`2/2 pass`（`TC-QA-PROC-001 pass`，`TC-QA-PROC-002 hold 路由 pass`）。
   - `python3 shared/registry/registry_contract_tool.py verify`：pass。
   - `openspec validate m3-meta-asset-quality-hardening --json`：pass。
2. 分发试点（phase-isolated-session）：
   - `quality_gate_evaluation_runner.py --enable-phase-dispatch` 在主链与 hold 路由均运行成功。
   - 当前模式先验证“分发证据链 + 隔离会话”，`dispatch_openclaw=false`（尚未开启真实 agent 分发）。
3. 自然语言结论：
   - QA 试点已证明“多会话协作主目标可运行”，当前主要缺口已从“能否协作”转为“如何规模化扩展到三条主流程并收敛 AP 迁移”。

## 9. Phase9（full-development 协作扩展 + 真实分发，新增）

### 目标

按用户确认策略推进首条主流程：`full-development` 必须在真实 OpenClaw 分发下运行，且同 actor 跨 phase 维持会话隔离。

### 输入

1. `processes/meta/full-development/{process.json,PROCESS.md,SKILL.md}`
2. `processes/meta/full-development/scripts/full_development_runner.py`（新增）
3. `skills/system/process-instance-manager/scripts/process_instance_runner.py`
4. `tests/m2-bpm-runtime/run_tc_full_dev_proc.py`（新增）

### 输出

1. full-development 协作骨架语义字段落盘（purpose/input/done/handoff）。
2. full-development 运行级 runner（真实 openclaw phase 分发 + 会话 reset）。
3. 运行级用例证据：`TC-FULL-DEV-PROC-001`。

### 子任务

- [x] 9.1 为 `full-development` 落盘协作策略与 phase 语义字段（`process.json` + 设计文档）。
- [x] 9.2 新增 `full_development_runner.py`，支持 8 phase 顺序分发与证据回放。
- [x] 9.3 为 `process-instance-manager` 增加会话 reset 与会话一致性校验能力。
- [x] 9.4 补充 `TC-FULL-DEV-PROC-001`，验证真实分发与同 actor 跨 phase 会话隔离。
- [x] 9.5 完成 design/inventory/registry/施工平面联动回写。

### DoD / 门禁

1. `python3 tests/m2-bpm-runtime/run_tc_full_dev_proc.py`
2. `python3 tests/m2-bpm-runtime/run_tc_qa_proc.py`
3. `python3 tests/m2-bpm-runtime/run_tc_hotfix_refactor_proc.py`
4. `python3 shared/registry/registry_contract_tool.py verify`
5. `openspec validate m3-meta-asset-quality-hardening --json`

### 执行结果（2026-02-23）

1. `python3 tests/m2-bpm-runtime/run_tc_full_dev_proc.py`：`1/1 pass`（`TC-FULL-DEV-PROC-001`）。
2. `python3 tests/m2-bpm-runtime/run_tc_qa_proc.py`：`2/2 pass`（回归通过，未引入回退）。
3. `python3 shared/registry/registry_contract_tool.py verify`：pass。
4. `openspec validate m3-meta-asset-quality-hardening --json`：pass。
5. 关键结论：
   - 8 个 phase 全部真实执行 openclaw 分发；
   - 同 actor 跨 phase 会话隔离校验通过（`actor_isolation_ok=true`）；
   - 协作主目标已从 QA 试点扩展到 `full-development` 主流程。

### 执行结果补充（2026-02-24）

1. `python3 tests/m2-bpm-runtime/run_tc_hotfix_refactor_proc.py`：`2/2 pass`。
2. `TC-HOTFIX-PROC-001`：`phase_count=7`，`dispatch_checks` 全通过，`actor_isolation_ok=true`。
3. `TC-REFACTOR-PROC-001`：`phase_count=6`，`dispatch_checks` 全通过，`actor_isolation_ok=true`。
4. 证据索引：`docs/design/modules/evidence/bpm-runtime/w3d_tc_hotfix_refactor_proc_report.json`。

## 10. Phase10（全量 AP 语义统一 + inline_ap 语法糖，新增）

### 目标

按用户最终决策完成“全量去 `target_type=skill`（含 control 流程）”，并引入临时 AP 语法糖以支持同 Actor 穿透执行。

### 输入

1. `processes/**/process.json`
2. `docs/architecture/process_architecture.md`
3. `docs/design/standards/process-definition-standard.md`
4. `docs/design/{interfaces,data-models}/**`
5. `shared/registry/registry_contract_tool.py`

### 输出

1. 全量流程 manifest：`target_type` 统一为 `subprocess`。
2. 对原 skill phase 增补 `inline_ap`（`ap_id/skill_id/actor/pierce_allowed`）。
3. 协议与标准文档同步到 `inline_ap` 语义。
4. registry/openspec 门禁通过。

### 子任务

- [x] 10.1 批量迁移 18 份 process manifest 的 skill phase 到 `subprocess + inline_ap`。
- [x] 10.2 更新协议与标准文档（process architecture / process definition / context schema / BPM actor protocol）。
- [x] 10.3 更新 `registry_contract_tool.py`，支持 `inline_ap` 校验与 M6 特殊门禁兼容。
- [x] 10.4 更新 inventory 与 construction plane 联动记录。
- [x] 10.5 执行 `registry verify + openspec validate + 关键运行回归`。
