# Admin Agent 详细设计

> 版本: v0.1.0 | agent_id: admin | 层级: kernel | 权限: system-root

## 1. 角色定位与权限

- **定位**: 系统所有者，最高权限持有者，升级决策的最终裁决者
- **owner**: human（人类管理员）
- **权限**: system-root — 可执行所有操作，包括修改其他 Agent 权限
- **原则**: SSOT 优先、Fail-Closed、最小惊讶

## 2. 绑定 Skill 清单

| Skill | 用途 | 状态 |
|---|---|---|
| release-manager | 发布管理 | 规划 |

> 此外，所有修改系统配置（openclaw.json）的Meta Skill，如 `system-config-updater` 只能由admin执行。
> 作为 main agent，admin可以使用所有技能。

## 3. 参与 Process 清单

| Process | 角色 | 说明 |
|---|---|---|
| development-process | 升级决策者 | 处理 escalation |
| lifecycle-review | 最终审批者 | 高权限状态转换审批 |
| escalation | 终点 | 升级链最终节点 |

> admin 主要通过决策和审批参与，较少直接执行流程。
> admin 拥有最高权限，可直接执行所有指令；所以App层Agent不能直接命令admin执行任务，而是通过Control层的BPM，遵照流程，经过BPM许可才能由BPM向admin提出系统级指令请求。

## 4. 协作关系

- **上级**: human（人类管理员）
- **下级**: architect, hr, qa（直接管理）
- **平级**: 无（最高层级）
- **特殊**: bpm 的 owner，可直接干预流程

## 5. 决策权限边界

| 决策类型 | 权限 |
|---|---|
| 架构变更 | 最终批准（architect 提案） |
| Agent 创建/退役 | 最终批准 |
| 升级处理 | 最终裁决 |
| 紧急停止 | 可直接执行 |
| 日常开发 | 不直接参与，委托给 architect/kernel-dev |

## 6. 记忆与上下文策略

- **持久记忆**: agents/kernel/admin/memory/ 日志
- **上下文来源**: construction_plane.md, escalation 记录
- **跨会话**: 通过文档传递，不依赖会话记忆
