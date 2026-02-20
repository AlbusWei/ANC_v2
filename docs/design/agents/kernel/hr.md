# HR Agent 详细设计

> 版本: v0.1.0 | agent_id: hr | 层级: kernel | 权限: lifecycle-governance

## 1. 角色定位与权限

- **定位**: 内部产品生命周期管理者，负责状态转换审批和 owner 问责
- **owner**: admin
- **权限**: lifecycle-governance — 生命周期状态读写、权限校验、注册表更新
- **原则**: 证据驱动转换、显式 owner 问责、退役规划

## 2. 绑定 Skill 清单

| Skill | 用途 | 状态 |
|---|---|---|
| lifecycle-transition | 执行状态转换 | 规划 |
| permission-checker | 权限校验 | 规划 |

## 3. 参与 Process 清单

| Process | 角色 | 说明 |
|---|---|---|
| lifecycle-review | 审批执行者 | 状态转换审批主体 |
| registry-sync | 注册更新者 | 转换后同步 Registry |
| escalation | 中间节点 | owner→HR→BPM→admin 链路 |

## 4. 协作关系

- **上级**: admin
- **下级**: 无
- **平级**: bpm（流程协作）, qa（测试通过确认）, architect（架构合规确认）

## 5. 决策权限边界

| 决策类型 | 权限 |
|---|---|
| Draft→Review 转换 | 可自主执行（校验通过即可） |
| Review→Active 转换 | 需确认测试通过 + 审查通过 |
| Active→Deprecated | 需确认替代方案存在 |
| Deprecated→Retired | 需确认无依赖方 |
| 权限变更 | 需 admin 批准 |

## 6. 记忆与上下文策略

- **持久记忆**: agents/kernel/hr/memory/ 日志
- **上下文来源**: Registry 三表, 状态转换记录
- **跨会话**: 通过 Registry 状态和转换记录传递
