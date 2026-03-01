# Software Vendor E2E Flow

> 版本: v0.5.0 | 层级: P4

## 目标

定义软件开发商承接客户需求、交付实施、验收交接和后续支持的业务主线，并在交付阶段强制复用内部 canonical 开发闭环。

## 阶段

1. lead-intake
2. discovery-analysis
3. solutioning-and-estimation
4. contract-baseline
5. delivery-iterations
6. customer-acceptance
7. deployment-and-handover
8. support-and-feedback

## 复用规则

1. `delivery-iterations` 必须组合 `docs/design/business/internal-productization-e2e-flow.md` 的核心开发闭环。
2. 其中质量门禁部分必须按连续性复用：
   - `docs/design/processes/quality-gate-preparation-process.md`
   - `docs/design/processes/quality-gate-evaluation-process.md`
3. HOLD 治理复用：`docs/design/processes/hold-governance-process.md`
4. 禁止旁路：未经过 `delivery-iterations` 不得直接进入交付或发布，命中则 Fail-Closed。

## 运行资产

1. process manifest：`processes/business/software-vendor-e2e-flow/process.json`
2. process 说明：`processes/business/software-vendor-e2e-flow/PROCESS.md`
3. 在线验证入口：`tests/m3-self-development/session6_external_runner.py`

## 阶段到原子流程映射

| 阶段 | 原子流程 |
|---|---|
| lead-intake | AP-001, AP-002 |
| discovery-analysis | AP-002, AP-003 |
| solutioning-and-estimation | AP-004, AP-005 |
| contract-baseline | AP-003 |
| delivery-iterations | AP-004~AP-012, AP-018~AP-025 |
| customer-acceptance | AP-016 |
| deployment-and-handover | AP-012, AP-016 |
| support-and-feedback | AP-013, AP-014, AP-015, AP-017 |

## 验收

- [ ] 业务端到端链路贯通
- [ ] 交付阶段复用内部开发闭环
- [ ] 客户验收有可追溯证据
