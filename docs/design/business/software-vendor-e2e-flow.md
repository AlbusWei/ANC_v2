# Software Vendor E2E Flow

> 版本: v0.3.0 | 层级: P4

## 定位

业务交付主线参考实现；`delivery-iterations` 阶段映射开发闭环标准义务。

## 目标

模拟软件开发商承接客户需求、开发、交付并持续服务的业务主线。

## 类型与规范绑定

1. 主流程可视为 `biz.*` 命名空间流程（预留）。
2. `delivery-iterations` 阶段建议使用 `phase_process_type=dev.external-delivery-iteration`。
3. 义务规则来源：`docs/design/processes/development-loop-core-standard.md`。

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

1. `delivery-iterations` 必须覆盖开发闭环标准义务（核心强制 + 条件触发）。
2. `internal-productization-e2e-flow` 仅为参考映射，不是规范依赖入口。
3. 复用链路必须保留父子实例引用和证据追溯。

## 阶段到义务映射（示例）

| 阶段 | Obligation |
|---|---|
| lead-intake + discovery-analysis | O1 Objective |
| solutioning-and-estimation | O2 Spec, O3 Test |
| delivery-iterations | O4 Implement, O5 Verify, O6 Lifecycle, O7 Release |
| support-and-feedback | O8 Evolution |

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
- [ ] `delivery-iterations` 义务覆盖可追溯到标准文档
- [ ] 客户验收有可追溯证据
