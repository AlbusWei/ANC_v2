# Agent Definition Standard

> 版本: v0.2.0 | 适用范围: 所有 Kernel/Control/App Agent

## 1. 目标

统一 Agent 设计文档与运行资产结构，确保角色边界清晰、权限可审计、交接可追溯。

## 2. 最小必填字段

1. `agent_id`（kebab-case，全局唯一）
2. `layer`（kernel|control|app）
3. `owner`（agent_id 或 human）
4. `permissions`（权限域）
5. `bound_skills`（skill_id 列表）
6. `participating_processes`（process_id 列表）
7. `decision_boundary`（可做/不可做）
8. `fail_closed_behavior`（失败后的升级链）

## 3. 文档结构

每个 Agent 设计文档必须包含：

1. 角色定位与权限
2. 绑定 Skill
3. 参与流程
4. 协作关系
5. 决策边界
6. 上下文策略
7. 验收标准

## 4. 与 Registry 咬合

1. 文档字段必须与 `/Users/albus/MyProjects/ANC_v2/shared/registry/agent_directory.json` 一致。
2. 生命周期状态统一为：`draft -> review -> active -> deprecated -> retired`。
3. owner 与 permissions 字段必须可映射到治理流程。

## 5. 验收条目

- [ ] 文档字段完整
- [ ] registry 引用一致
- [ ] 升级链定义明确
- [ ] 参与流程可追溯到 process inventory
