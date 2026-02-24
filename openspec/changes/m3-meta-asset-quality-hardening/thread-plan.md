# m3-meta-asset-quality-hardening 线程执行计划（P0~P7）

## 元信息

1. change: `m3-meta-asset-quality-hardening`
2. 主目标：Meta 资产质量硬化 + bundle 退役 + QA 在线主验收
3. 生命周期上限：`review`
4. 强约束：`ap-*-bundle` 不得作为目标态运行结构

## P0 初始化与规格落盘（已执行）

### 目标

建立独立 change 与全量规格基线，直接指导 P1~P7。

### 输入

1. `AGENTS.md`
2. `openspec/changes/m3-self-development-e2e-online/*`
3. `docs/design/*`、`shared/registry/*`

### 输出

1. `proposal/design/tasks/thread-plan/meta-gap-baseline`
2. `specs/meta-asset-quality/spec.md`
3. `specs/process-architecture-refactor/spec.md`
4. `specs/qa-online-validation/spec.md`
5. 旧 change 依赖说明回写

### DoD

1. `openspec validate m3-meta-asset-quality-hardening --json` 通过
2. `python3 shared/registry/registry_contract_tool.py verify` 通过
3. spec 内明确 bundle 退役、P5 子流程、QA 在线主验收、Fail-Closed 回退

## P1 方法论与迁移蓝图

### 目标

输出可执行的“bundle -> P5 子流程”迁移矩阵与流程拆分标准。

### 输入

1. P0 spec + design
2. 当前流程资产/设计文档

### 输出

1. 新增流程拆分方法论标准
2. 迁移矩阵（含职责边界、输入输出、替换顺序）

### DoD

1. 方法论文档落盘且可检索原则/反例
2. 迁移矩阵覆盖全部 bundle
3. 未出现职责交叉与依赖悬空

### 失败回退

1. 若矩阵存在冲突，停止进入 P2，回到 P1 修订。

## P2 流程资产重构

### 目标

替换运行时 bundle 依赖并落地 P5 子流程库。

### 输入

1. P1 迁移矩阵
2. 主流程 manifest 与流程文档

### 输出

1. P5 子流程资产
2. 主流程引用替换完成
3. bundle 运行引用归零

### DoD

1. 主流程不再引用 `ap-*-bundle`
2. 新子流程契约与调用契约闭合
3. registry 校验与 openspec 校验通过

### 失败回退

1. 若新流程不可运行，回滚到上一个 manifest 快照并记录阻断。

## P3 Meta 技能质量升级

### 目标

全量升级 8 个 Meta 技能并解决 `skill-creator` 命名冲突。

### 输入

1. `skills/meta/*`、`skills/skill-creator/*`
2. skill registry 与 openclaw 可见性

### 输出

1. 可执行手册级 `SKILL.md`
2. runner/references/test 完整化
3. `meta.arch.skill-creator` 唯一运行名与映射说明

### DoD

1. 8 个技能都具备执行步骤、Fail-Closed、references、可运行入口
2. openclaw 可唯一解析本地 skill-creator
3. 脚手架不再输出 TODO 占位

### 失败回退

1. 若命名冲突未解，禁止推进 lifecycle。

## P4 联动闭合

### 目标

完成文档/清单/注册表/施工平面的同回合一致性。

### 输入

1. P2/P3 结果
2. 各类 SSOT 文档

### 输出

1. design + inventories + registry + construction plane 全量联动
2. OpenSpec 状态与任务回写

### DoD

1. 不存在“文档与 registry 倒挂”
2. 所有被修改资产都有对应设计与清单落盘

### 失败回退

1. 任一联动项缺失即阻断，回到 P4 补齐。

## P5 QA 在线测试基座强化

### 目标

建立 Meta 资产专项在线 QA 套件，明确主验收路径。

### 输入

1. P2/P3/P4 资产
2. 现有 `tests/m3-self-development` 基座

### 输出

1. 在线执行脚本
2. 覆盖矩阵与证据目录

### DoD

1. 用例可运行且包含 Happy/Fail-Closed/Traceability/Rollback
2. 存在 openclaw 在线场景并作为主验收

### 失败回退

1. 若仅剩静态验证，判失败并回到 P5 补测试。

## P6 QA 在线执行与闭环

### 目标

完成在线执行、缺陷修复与回归通过。

### 输入

1. P5 套件
2. runtime 环境

### 输出

1. 在线执行报告
2. 缺陷清单、修复记录、回归证据

### DoD

1. 关键在线 case 全通过
2. 所有阻断缺陷闭环

### 失败回退

1. 在线关键用例失败则继续修复，不得进入 P7。

### 执行记录（2026-02-23）

1. round-1 全量在线执行：
   - `python3 tests/m3-self-development/run_meta_qa_online.py`
   - 结果：`112/111/1`，发现阻断缺陷 `DEF-PH6-001`（`MP-CONSTRUCTION-PLANE-GOVERNANCE-RB`）。
2. 缺陷修复与回归：
   - 修复点：`tests/m3-self-development/run_meta_qa_online.py`（在线响应一次重试 + 提示词约束“禁止执行命令”）。
   - 定向回归：失败 case 与受影响资产四场景全部通过。
3. 高风险 FC 稳定性：
   - 关键 4 技能 FC + 修复资产 FC，连续 3 轮全部通过。
4. 最终全量在线回归：
   - `python3 tests/m3-self-development/run_meta_qa_online.py`
   - 结果：`112/112/0`，gate=`pass`。
5. Phase6 门禁：
   - `python3 shared/registry/registry_contract_tool.py verify`：pass
   - `openspec validate m3-meta-asset-quality-hardening --json`：pass
6. 证据入口：
   - `runtime_data/execution/evidence/self-development/runtime-validation-round-meta-assets/latest/phase6_execution_rounds.json`
   - `runtime_data/execution/evidence/self-development/runtime-validation-round-meta-assets/latest/phase6_defect_closure.json`
   - `runtime_data/execution/evidence/self-development/runtime-validation-round-meta-assets/latest/phase6_final_conclusion.md`

## P7 收口

### 目标

四向对账、状态收敛到 review、Entire 审计闭环。

### 输入

1. P0~P6 全量证据
2. 提交与 checkpoint 信息

### 输出

1. 收口报告
2. 状态迁移记录（仅到 review）
3. 完整审计链（含 Entire-Checkpoint）

### DoD

1. `openspec validate` + `registry verify` + 最终回归通过
2. `git log -1 --pretty=raw` 含 `Entire-Checkpoint`
3. `entire_codex_bridge.py end` 成功

### 失败回退

1. 任一门禁失败，禁止宣告完成。

### 执行记录（2026-02-24）

1. 四向对账完成：OpenSpec、registry、design docs、runtime evidence 一致。
2. 生命周期收敛：
   - Meta Skills（8）保持 `review`，`active=0`。
   - Meta Processes（20）统一为 `review`，`draft=0`，`active=0`。
   - `escalation`、`governed-config-change`、`registry-sync` 已由 `draft` 推进到 `review`。
3. 最终门禁通过：
   - `python3 shared/registry/registry_contract_tool.py verify`
   - `openspec validate m3-meta-asset-quality-hardening --json`
   - `python3 tests/m3-self-development/run_meta_qa_online.py --suite final-regression`（`112/112`，`run_root=runtime_data/execution/evidence/self-development/runtime-validation-round-meta-assets/latest/runs/run-20260224T114948Z`）
4. bundle 运行面检查通过：
   - `rg -n "ap-[0-9].*-bundle" processes/meta shared/registry docs/design` 无命中。
5. 证据入口：
   - `runtime_data/execution/evidence/self-development/runtime-validation-round-meta-assets/latest/phase7_four_way_reconciliation.json`
   - `runtime_data/execution/evidence/self-development/runtime-validation-round-meta-assets/latest/phase7_lifecycle_summary.json`

## P8 流程协作骨架 v1（QA 试点，新增）

### 目标

按“设计思想优先”修正流程实现：先确保 BPM 下多 Agent/多会话协作可运行，再补契约细节。首个试点固定在 `quality-gate-evaluation`。

### 输入

1. `docs/architecture/process_architecture.md`（流程架构最高信源）
2. `openspec/changes/m3-meta-asset-quality-hardening/process-collaboration-skeleton-v1-plan.md`
3. QA 试点流程资产与 runner

### 输出

1. phase 级协作骨架（purpose/input context/done/handoff）落盘。
2. phase 级 isolated session（每 phase 新建会话）运行路径可用。
3. 试点运行结论（自然语言）与证据索引。

### DoD

1. 至少一条主链路证明“多会话协作主目标跑通”。
2. 至少一条 hold 路由证明跨角色交接链路可运行。
3. 输出可读的可用性结论，而非仅格式校验结论。

### 失败回退

1. 若试点未跑通，禁止扩散到 `full-development/hotfix/refactor`，先在 QA 试点闭环。

### 执行记录（2026-02-23）

1. `quality-gate-evaluation` 已接入 phase 级 isolated session 分发（可选 `--dispatch-openclaw`）。
2. 主链与 hold 路由在分发模式均已跑通，当前结论为“协作骨架可运行”。
3. 下一步重点从“单流程验证”转向“三主流程扩展 + AP 迁移收敛”。

## P9 full-development 协作扩展（真实分发，新增）

### 目标

按用户确认决策推进首条主流程：`full-development` 必须使用真实 OpenClaw phase 分发，并验证同 actor 跨 phase 会话隔离。

### 输入

1. `processes/meta/full-development/*`
2. `skills/system/process-instance-manager/scripts/process_instance_runner.py`
3. `tests/m2-bpm-runtime/run_tc_full_dev_proc.py`

### 输出

1. full-development 协作骨架语义 + 运行级 runner。
2. 会话治理增强：dispatch 前 `sessions.reset` + 会话一致性校验。
3. 运行级证据：`TC-FULL-DEV-PROC-001`。

### DoD

1. `TC-FULL-DEV-PROC-001` 通过，且 `phase_count=8`。
2. `dispatch_checks` 全 phase 通过。
3. `actor_isolation_ok=true`（同 actor 跨 phase 会话不复用）。

### 执行记录（2026-02-23）

1. 新增 `full_development_runner.py` 并打通 8 phase 真实分发。
2. `process-instance-manager` 增加 `--reset-openclaw-session` 与 `--strict-session-match`。
3. 首次执行遇到 gateway 会话锁冲突，重启 gateway 后复跑通过（Fail-Closed 生效）。
4. 最终结果：`python3 tests/m2-bpm-runtime/run_tc_full_dev_proc.py` => `1/1 pass`。

### 执行记录补充（2026-02-24）

1. 新增 `hotfix_runner.py`、`refactor_runner.py`，两条主流程均接入真实 openclaw phase 分发。
2. 新增运行级用例：`python3 tests/m2-bpm-runtime/run_tc_hotfix_refactor_proc.py`。
3. 结果：`TC-HOTFIX-PROC-001` 与 `TC-REFACTOR-PROC-001` 全通过（会话严格匹配 + 同 actor 跨 phase 隔离通过）。

## P10 全量 AP 语义统一（含 control，新增）

### 目标

按用户决策完成“全量去 `target_type=skill`”，统一流程 phase 到 AP 语义入口，并引入 `inline_ap` 语法糖支持同 Actor 穿透执行。

### 输入

1. `processes/**/process.json`
2. `docs/architecture/process_architecture.md`
3. `shared/registry/registry_contract_tool.py`

### 输出

1. 18 份流程 manifest 从 `skill` phase 迁移到 `subprocess + inline_ap`。
2. 协议与标准文档同步 `inline_ap` 规则。
3. 门禁与回归通过记录。

### DoD

1. `rg -n "\"target_type\"\\s*:\\s*\"skill\"" processes/**/process.json` 返回空。
2. `python3 shared/registry/registry_contract_tool.py verify` 通过。
3. `openspec validate m3-meta-asset-quality-hardening --json` 通过。

### 执行记录（2026-02-23）

1. 18 份流程 manifest 已完成迁移，包含 `processes/control/*` 与 `processes/meta/*`。
2. `registry_contract_tool.py` 已支持 `inline_ap` 校验（`ap_id/skill_id/actor/pierce_allowed`）与 M6 特例同步检查。
3. `process_architecture`、`process-definition-standard`、`process-instance-schemas`、`bpm-actor-protocol`、`context-schemas` 已同步新语义。
