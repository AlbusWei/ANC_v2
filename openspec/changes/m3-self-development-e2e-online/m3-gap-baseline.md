# M3 设计闭合差距矩阵（Session4 更新）

> round_id: `R-20260222-M6-m3-self-development-e2e-online-01`

| 设计条目 | 应有资产 | 现状 | 阻断级别 | 归属会话 | 状态 | 验收条件 |
|---|---|---|---|---|---|---|
| full-development phase 执行语法应仅引用子流程/AP（设计） | `docs/design/processes/full-development-process.md` 目标态映射表 | 已补齐治理绑定蓝图与 phase 目标态表 | S0 | Session2 | closed（design） | 文档中可追溯 `phase->AP/子流程` 目标态 |
| full-development phase 执行语法应仅引用子流程/AP（实现） | `processes/meta/full-development/process.json` | 已改造为 `target_type=subprocess` 并绑定 AP 包装流程 | S1 | Session3 | closed（implementation） | manifest 不再出现 phase 直连 skill |
| hotfix phase 执行语法应仅引用子流程/AP（设计） | `docs/design/processes/hotfix-process.md` 目标态映射表 | 已补齐治理绑定蓝图与 phase 目标态表 | S0 | Session2 | closed（design） | 文档中可追溯 `phase->AP/子流程` 目标态 |
| hotfix phase 执行语法应仅引用子流程/AP（实现） | `processes/meta/hotfix/process.json` | 已改造为 `target_type=subprocess` 并绑定 AP 包装流程 | S1 | Session3 | closed（implementation） | manifest 不再出现 phase 直连 skill |
| refactor phase 执行语法应仅引用子流程/AP（设计） | `docs/design/processes/refactor-process.md` 目标态映射表 | 已补齐治理绑定蓝图与 phase 目标态表 | S0 | Session2 | closed（design） | 文档中可追溯 `phase->AP/子流程` 目标态 |
| refactor phase 执行语法应仅引用子流程/AP（实现） | `processes/meta/refactor/process.json` | 已改造为 `target_type=subprocess` 并绑定 AP 包装流程 | S1 | Session3 | closed（implementation） | manifest 不再出现 phase 直连 skill |
| M3 三流程 `process_type` 治理绑定（设计） | 三流程设计文档 | 已固定 `dev.internal-productization/dev.hotfix/dev.refactor` | S0 | Session2 | closed（design） | 三份流程文档均声明固定 `process_type` |
| M3 三流程 `process_type` 治理绑定（实现） | 三流程 manifest | 已补齐 `process_type` 字段 | S1 | Session3 | closed（implementation） | 三流程 manifest 均新增 `process_type` |
| M3 三流程 `governance_bundle` 治理绑定（设计） | 三流程设计文档 | 已补 `syntax_ref/obligation_ref/risk_policy_ref/checklist_ref` 引用 | S0 | Session2 | closed（design） | 三份流程文档均包含固定 `governance_bundle` 引用 |
| M3 三流程 `governance_bundle` 治理绑定（实现） | 三流程 manifest | 已补齐 `governance_bundle` 字段并指向可达文档 | S1 | Session3 | closed（implementation） | 三流程 manifest 均新增 `governance_bundle` 且引用可达 |
| AP 包装流程族（实现） | `processes/meta/ap-*-bundle/` + process registry 条目 | 7 个 AP 包装流程已落地并注册 | S1 | Session3 | closed（implementation） | 包装流程可调度、生命周期保持 `draft` |
| `sys.arch.impact-analyzer` 定义卡（设计） | `docs/design/skills/system-skills.md` + `docs/design/skills/self-development-skills.md` | 已补输入/输出/Fail-Closed/test_mount/lifecycle | S0 | Session2 | closed（design） | 契约字段齐全，生命周期目标为 `draft` |
| `sys.arch.impact-analyzer` 运行资产（实现） | `skills/system/impact-analyzer/` + registry 条目 | 已落地运行目录与 registry 实条目 | S1 | Session3 | closed（implementation） | 目录存在，`skill_registry.json` 新增条目，`registry verify` 通过 |
| `sys.admin.release-manager` 定义卡（设计） | `docs/design/skills/system-skills.md` + `docs/design/skills/self-development-skills.md` | 已补输入/输出/Fail-Closed/test_mount/lifecycle | S0 | Session2 | closed（design） | 契约字段齐全，生命周期目标为 `draft` |
| `sys.admin.release-manager` 运行资产（实现） | `skills/system/release-manager/` + registry 条目 | 已落地运行目录与 registry 实条目 | S1 | Session3 | closed（implementation） | 目录存在，`skill_registry.json` 新增条目，`registry verify` 通过 |
| `registry-sync` 流程设计（设计） | `docs/design/processes/registry-sync-process.md` | 已按 P6/AP-011 口径闭合 | S0 | Session2 | closed（design） | 文档含输入/输出/Fail-Closed/test_mount/生命周期 |
| `registry-sync` 运行资产（实现） | `processes/meta/registry-sync/` + process registry 条目 | 已落地运行目录与 registry 条目 | S1 | Session3 | closed（implementation） | 目录存在，`process_registry.json` 新增条目，`registry verify` 通过 |
| `escalation` 流程设计（设计） | `docs/design/processes/escalation-process.md` | 已按 P5 子流程口径闭合 | S0 | Session2 | closed（design） | 文档含固定 phase/AP 映射、升级链与契约字段 |
| `escalation` 运行资产（实现） | `processes/meta/escalation/` + process registry 条目 | 已落地运行目录与 registry 条目 | S1 | Session3 | closed（implementation） | 目录存在，`process_registry.json` 新增条目，`registry verify` 通过 |
| `release-manager-agent` 设计口径升级（设计） | `docs/design/agents/app/delivery/release-manager-agent.md` + inventory 联动 | 已补 `bound_skills/participating_processes/handoff` 双输出 | S0 | Session2 | closed（design） | 文档可直接映射到运行资产模板 |
| `release-manager-agent` 运行资产（实现） | `agents/app/delivery/release-manager-agent/` + `agent_directory.json` 条目 | 已落地运行目录与 registry 条目 | S1 | Session3 | closed（implementation） | 目录存在，`agent_directory.json` 新增条目，`registry verify` 通过 |
| Session3 技能契约验证入口 | `tests/m3-runtime/`（TEST + runner + evidence） | 已创建并覆盖两技能 happy/fail-closed 核心路径 | S1 | Session3 | closed（implementation） | `python3 tests/m3-runtime/run_skill_contract_validation.py` 可执行且报告写入 evidence 目录 |
| Session4 M3 专项测试基座（可复用 runner + 用例体系） | `tests/m3-self-development/{TEST.md,live_cases.md,run_tc_online.py}` + `runtime_data/execution/evidence/self-development/e2e-online/session4-foundation/latest/` | 已落地单 runner（`--suite/--case`），默认覆盖主链路/异常链路/Fail-Closed/回退返工四类；已预留 `M3-INT-*`/`M3-EXT-*`/`M3-FC-*` 供 Session5/6 复用 | S1 | Session4 | closed（implementation） | `python3 tests/m3-self-development/run_tc_online.py --help` 通过；默认执行产生四类断言证据；预留 case 在 Session4 强制执行时 Fail-Closed |
| 内部主线 E2E 尚未执行 | 内部主线 E2E 证据包（M3 canonical） | 尚未形成证据 | S2 | Session5 | open | 内部主线关键场景通过并可回退 |
| 外部主线 E2E 尚未执行 | 外部主线 E2E 证据包（复用 M3 canonical） | 尚未形成证据 | S2 | Session6 | open | 外部主线关键场景通过且无旁路 |
