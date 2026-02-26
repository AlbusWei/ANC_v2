# software-vendor-e2e-flow-process

> process_id: `software-vendor-e2e-flow` | 层级: `P4` | 类型: `dev.external-delivery-iteration` | 生命周期目标: `draft`

## 流程目标

`software-vendor-e2e-flow` 位于外部软件交付主线，负责把“商机输入 -> 需求澄清 -> 合同基线 -> 交付迭代 -> 验收交接 -> 支持反馈”收敛为一条可执行、可审计、可复用的流程链。它要解决的问题是外部交付常见的旁路发布风险：在合同和质量门禁未闭合时直接进入交付。对上下游的交付价值是：

1. 上游销售/架构可获得可执行的合同与范围边界。
2. 下游交付/运维可获得带门禁和回滚证据的发布输入。
3. 下一轮迭代可直接复用支持反馈与改进建议。

## 关键约束

1. `delivery-iterations` 必须复用 canonical `full-development`，不得脚本直连发布。
2. 关键门禁链路必须可追溯：`quality-gate-preparation -> quality-gate-evaluation -> lifecycle-review -> registry-sync`。
3. Session6 生命周期结论上限为 `review`，越级尝试到 `active` 必须 Fail-Closed。

## Phase 映射（8 段）

| phase_id | 阶段 | target_type | target_id | 语义说明 |
|---|---|---|---|---|
| p1 | lead-intake | subprocess | objective-scope-baseline | 商机输入收敛为可执行 objective/scope |
| p2 | discovery-analysis | subprocess | objective-scope-baseline | 需求发现与边界约束补齐 |
| p3 | solutioning-and-estimation | subprocess | spec-authoring-contract | 方案与估算规格生成 |
| p4 | contract-baseline | subprocess | spec-authoring-contract | 合同边界与回退约束固化 |
| p5 | delivery-iterations | subprocess | full-development | 外部交付迭代，强制复用 canonical |
| p6 | customer-acceptance | subprocess | quality-gate-evaluation | 客户验收证据收敛 |
| p7 | deployment-and-handover | subprocess | release-packaging-governed | 部署交接与回滚包绑定 |
| p8 | support-and-feedback | subprocess | evolution-feedback-planning | 支持反馈回灌下一轮 |

## Fail-Closed 语义

1. 缺失 `final_gate_verdict_ref/lifecycle_transition_ref/registry_sync_ref` 任一关键引用：拒绝推进。
2. 检测到 `delivery-iterations` 旁路：拒绝推进。
3. 生命周期越级尝试（`review -> active`）：拒绝推进。

## 运行与验证

1. manifest：`processes/business/software-vendor-e2e-flow/process.json`
2. 在线 runner：`tests/m3-self-development/session6_external_runner.py`
3. 套件入口：`tests/m3-self-development/run_tc_online.py --suite session6-external`
