# M4 — 生命周期管理模块详细设计

> 版本: v0.4.0 | 建设优先级: P1

## 模块定位

M4 管理内部产品版本实例（`ProductVersionInstance`）的生命周期迁移、审批证据与版本角色切换，确保产品定义与实现绑定一致。

## 核心对象

1. `Product`
2. `ProductVersionInstance`（主键：`product_id + branch_or_worktree_id`）
3. `ProductAssetBinding`
4. `VersionRoleTag`（`developing | active | legacy`）

## 生命周期循环（非线性）

`idea -> design -> build -> verify -> operate -> observe -> evolve -> design/build`

治理终止路径：`deprecate -> retire`

## 多版本并存规则

1. 同一 `product_id` 允许多个 `ProductVersionInstance` 并存。
2. 每个实例独立推进生命周期状态。
3. `VersionRoleTag` 用于标记实例角色，支持并行 `developing/active/legacy`。
4. 版本切换必须附带证据链：验证结果、风险评估、回滚策略。

## 与 M5 / M3 / M1 的边界

1. M4 负责治理放行与角色切换，不替代 M3 的开发执行。
2. M4 接收 M5 的演化提案结果并执行状态迁移。
3. M4 复用 M1 验证证据作为放行输入。

## Fail-Closed 约束

1. 缺少 `goal/consumer/scope/acceptance/version_policy` 的 `Product` 不得进入治理流。
2. 缺少验证证据或回滚策略的角色切换请求必须拒绝。
3. 仅当涉及系统级高风险例外时引入 `admin` 审批，常规迁移由 `hr` 执行并签署。

## 与 registry 5 态兼容

1. registry 层仍保持资产 5 态（`draft/review/active/deprecated/retired`）。
2. M4 新增的是“产品版本实例生命周期”语义层，不替代 registry 资产状态机。

## 验收

- [ ] 生命周期循环与治理终止路径可追溯
- [ ] 支持同产品多版本并存且实例独立推进
- [ ] 版本角色切换具备完整证据链
- [ ] 产品定义准入缺失时 fail-closed 生效
