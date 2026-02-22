# M3 设计闭合差距矩阵（Session1 基线）

> round_id: `R-20260222-M6-m3-self-development-e2e-online-01`

| 设计条目 | 应有资产 | 现状 | 阻断级别 | 归属会话 | 验收条件 |
|---|---|---|---|---|---|
| full-development phase 执行语法应仅引用子流程/AP | `processes/meta/full-development/process.json` phase target 仅为 subprocess/AP，且有义务映射追溯 | 当前 phase 仍存在 `target_type=skill` 直连 | S0 | Session2 | manifest 更新后无 phase 直连 skill；差距项在 design/specs 中标记 closed |
| hotfix phase 执行语法应仅引用子流程/AP | `processes/meta/hotfix/process.json` phase target 仅为 subprocess/AP，且有义务映射追溯 | 当前 phase 仍存在 `target_type=skill` 直连 | S0 | Session2 | manifest 更新后无 phase 直连 skill；`openspec validate` 通过 |
| refactor phase 执行语法应仅引用子流程/AP | `processes/meta/refactor/process.json` phase target 仅为 subprocess/AP，且有义务映射追溯 | 当前 phase 仍存在 `target_type=skill` 直连 | S0 | Session2 | manifest 更新后无 phase 直连 skill；差距项状态 closed |
| M3 三流程 `process_type` 治理绑定 | `full-development/hotfix/refactor` 均包含 `process_type` | 目前三流程 manifest 缺失 `process_type` | S0 | Session2 | 三流程 manifest 均新增 `process_type` 且值属于标准枚举 |
| M3 三流程 `governance_bundle` 治理绑定 | 三流程 manifest 均包含 `governance_bundle.{syntax_ref,obligation_ref,risk_policy_ref,checklist_ref}` | 目前三流程 manifest 缺失 `governance_bundle` | S0 | Session2 | 三流程 manifest 均新增 `governance_bundle` 且引用可达 |
| `sys.arch.impact-analyzer` 设计已声明但未落地 | `skills/system/impact-analyzer/` + 设计文档 + registry + test_mount | 仅在 design/inventory 中规划，资产目录缺失 | S1 | Session3 | 技能目录存在；`skill_registry.json` 有条目；`registry verify` 通过 |
| `sys.admin.release-manager` 设计已声明但未落地 | `skills/system/release-manager/` + 设计文档 + registry + test_mount | 仅在 design/inventory 中规划，资产目录缺失 | S1 | Session3 | 技能目录存在；`skill_registry.json` 有条目；`registry verify` 通过 |
| `registry-sync` process 规划存在但未落地 | `processes/meta/registry-sync/` + process doc + inventory + process_registry | 仅在 process inventory/governance docs 规划，流程资产缺失 | S1 | Session3 | 流程目录存在；`process_registry.json` 新增条目；`registry verify` 通过 |
| `escalation` process 规划存在但未落地 | `processes/meta/escalation/` + process doc + inventory + process_registry | 升级语义散落在多流程中，独立治理流程资产缺失 | S1 | Session3 | 流程目录存在；`process_registry.json` 新增条目；`registry verify` 通过 |
| `release-manager-agent` 设计文档存在但未落地运行资产 | `agents/app/delivery/release-manager-agent/` 运行目录 + agent_directory + inventory | 仅有设计文档，agent 运行目录与 registry 条目缺失 | S1 | Session3 | agent 目录存在；`agent_directory.json` 新增条目；`registry verify` 通过 |
| M3 专项运行级测试套件未成体系 | `tests/m3-self-development/`（TEST + runner + case 索引）与证据目录 | 当前仅有 `tests/development-process/TEST.md` 与 M1/M2 链路验证 | S2 | Session4 | M3 测试套件目录与入口落盘；至少 1 个 online case 可执行；Fail-Closed 路径有证据 |
| 内部主线 E2E 尚未执行 | 内部主线 E2E 证据包（M3 canonical） | 尚未形成内部主线运行证据 | S2 | Session5 | 内部主线 E2E 关键场景通过并有可回退证据 |
| 外部主线 E2E 尚未执行 | 外部主线 E2E 证据包（复用 M3 canonical） | 尚未形成外部主线运行证据 | S2 | Session6 | 外部主线 E2E 通过且无旁路；复用映射证据完备 |
