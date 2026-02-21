# 业务流程设计

> 版本: v0.3.0 | 分类: Business Processes | 层级: L5

## 双主线（参考实现）

1. 内部产品孵化（reference example）：`/Users/albus/MyProjects/ANC_v2/docs/design/business/internal-productization-e2e-flow.md`
2. 外部软件交付（reference example）：`/Users/albus/MyProjects/ANC_v2/docs/design/business/software-vendor-e2e-flow.md`

## 规范真相来源

1. 开发闭环标准：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/development-loop-core-standard.md`
2. 递归语义标准：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/recursive-process-architecture.md`
3. P4→P6 统一追溯表：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/p4-p6-obligation-traceability-matrix.md`

## 复用约束

1. 外部交付主线的 `delivery-iterations` 必须复用开发闭环标准义务，而非绑定单一示例流程文档。
2. `internal-productization-e2e-flow` 仅提供参考映射，可替换但不得改变标准语义。
3. 复用节点必须保留父子实例引用与证据链。

## P1-P6 映射

业务流程位于 P4，依赖 P5 模式和 P6 原子流程。

## 流程语法约束

1. `phase` 只能组合子流程（复合或原子），不允许直接调用 skill。
2. 任意 skill 调用必须包装为原子流程并受 I/O 与证据契约约束。

## 激活前置

1. 流程定义符合 process standard。
2. 通过 lifecycle-review。
3. 在 process_registry 注册并进入 review。
4. 开发型流程的 `process.json` 必须声明 `process_type` 与 `governance_bundle` 引用。
