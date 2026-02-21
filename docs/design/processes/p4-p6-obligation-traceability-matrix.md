# P4-P6 Obligation Traceability Matrix

> 版本: v0.1.0 | 作用域: P4 端到端流程到 P6 原子流程追溯

## 1. 目的

1. 作为本分支 DoD 的统一追溯表，展示 P4 阶段如何映射到标准义务与 P6 原子流程。
2. 支持“标准合规 + 证据可审计 + Fail-Closed 可执行”联合核对。

## 2. 规范来源

1. 义务与触发规则：`docs/design/processes/development-loop-core-standard.md`
2. 示例流程：
   - `docs/design/business/internal-productization-e2e-flow.md`
   - `docs/design/business/software-vendor-e2e-flow.md`
3. 原子流程目录：`docs/design/processes/p-levels/P6-atomic-process-catalog.md`

## 3. Trace Matrix

| P4 流程 | 阶段 | Obligation | P6 原子流程 | 关键证据（示例） | Fail-Closed 动作 |
|---|---|---|---|---|---|
| internal-productization-e2e-flow | objective-intake | O1 Objective | AP-001, AP-002, AP-003 | `objective_ref`, `requirement_report_ref`, `scope_baseline_ref` | 目标/范围不完整则阻断进入 spec |
| internal-productization-e2e-flow | spec-authoring | O2 Spec | AP-004 | `spec_ref` | Spec 不可验证则阻断进入 test |
| internal-productization-e2e-flow | test-design | O3 Test | AP-005 | `test_plan_ref` | P0 用例缺失则阻断实现 |
| internal-productization-e2e-flow | implementation-execution | O4 Implement | AP-006 | `implementation_ref` | 与 spec 不可追溯则退回 |
| internal-productization-e2e-flow | objective-evaluation | O5 Verify | AP-007, AP-008, AP-009 | `objective_verdict_ref`, `subjective_eval_ref`, `regression_report_ref` | 判定失败或回归失败则阻断 lifecycle/release |
| internal-productization-e2e-flow | lifecycle-review | O6 Lifecycle | AP-010, AP-011 | `lifecycle_transition_ref`, `registry_sync_ref` | 非法状态迁移或 registry 校验失败则拒绝推进 |
| internal-productization-e2e-flow | release-packaging | O7 Release | AP-012 | `release_package_ref` | 门禁缺失则拒绝发布 |
| internal-productization-e2e-flow | evolution-feedback | O8 Evolution | AP-013, AP-014, AP-015, AP-017 | `incident_triage_ref`, `rca_report_ref`, `improvement_plan_ref`, `retro_report_ref` | 证据不足则不允许关闭问题或进入新迭代 |
| software-vendor-e2e-flow | lead-intake + discovery-analysis | O1 Objective | AP-001, AP-002, AP-003 | `objective_ref`, `requirement_report_ref`, `scope_baseline_ref` | 需求冲突/范围不清则阻断 solutioning |
| software-vendor-e2e-flow | solutioning-and-estimation | O2 Spec + O3 Test | AP-004, AP-005 | `spec_ref`, `test_plan_ref` | 不可验证方案或缺关键测试则阻断交付迭代 |
| software-vendor-e2e-flow | delivery-iterations | O4 Implement + O5 Verify + O6 Lifecycle + O7 Release | AP-004~AP-012 | `implementation_ref`, `objective_verdict_ref`, `regression_report_ref`, `lifecycle_transition_ref`, `registry_sync_ref`, `release_package_ref` | 任一门禁失败则阻断进入验收/交付 |
| software-vendor-e2e-flow | customer-acceptance + deployment-and-handover | O7 Release | AP-012, AP-016 | `release_package_ref`, `acceptance_result_ref` | 验收失败则拒绝签收与移交 |
| software-vendor-e2e-flow | support-and-feedback | O8 Evolution | AP-013, AP-014, AP-015, AP-017 | `incident_triage_ref`, `rca_report_ref`, `improvement_plan_ref`, `retro_report_ref` | 无证据复盘或根因不成立则阻断改进闭环 |

## 4. 覆盖性检查（本版）

1. 两条 P4 主线均已覆盖至 P6。
2. O1~O6 为核心强制义务，O7/O8 按标准触发并在两条示例主线中均已落地。
3. AP-001~AP-017 在双主线中均有可追溯落点。
