# 业务流程设计

> 版本: v0.3.0 | 分类: Business Processes | 层级: L5

## 双主线

1. 内部产品孵化：`docs/design/business/internal-productization-e2e-flow.md`
2. 外部软件交付：`docs/design/business/software-vendor-e2e-flow.md`

## 复用约束

外部交付主线的 `delivery-iterations` 必须复用内部孵化主线的开发闭环。

## 运行资产映射

1. 外部主线流程资产：`processes/business/software-vendor-e2e-flow/process.json`
2. 运行说明：`processes/business/software-vendor-e2e-flow/PROCESS.md`
3. 生命周期目标：`draft`（Session6 仅做运行验证，不推进到 `active`）

## P1-P6 映射

业务流程位于 P4，依赖 P5 模式和 P6 原子流程。

## 激活前置

1. 流程定义符合 process standard。
2. 通过 lifecycle-review。
3. 在 process_registry 注册并进入 review。
