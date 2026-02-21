# Software Vendor E2E Flow

> 版本: v0.2.0 | 层级: P4

## 目标

模拟软件开发商承接客户需求、开发、交付并持续服务的业务主线。

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

`delivery-iterations` 必须组合 `docs/design/business/internal-productization-e2e-flow.md` 的核心开发闭环。

## 阶段到原子流程映射

| 阶段 | 原子流程 |
|---|---|
| lead-intake | AP-001, AP-002 |
| discovery-analysis | AP-002, AP-003 |
| solutioning-and-estimation | AP-004, AP-005 |
| contract-baseline | AP-003 |
| delivery-iterations | AP-004~AP-012 |
| customer-acceptance | AP-016 |
| deployment-and-handover | AP-012, AP-016 |
| support-and-feedback | AP-013, AP-014, AP-015, AP-017 |

## 验收

- [ ] 业务端到端链路贯通
- [ ] 交付阶段复用内部开发闭环
- [ ] 客户验收有可追溯证据
