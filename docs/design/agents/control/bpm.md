# BPM Agent 详细设计

> 版本: v0.1.0 | agent_id: bpm | 层级: control | 权限: orchestration-control

## 1. 角色定位与权限

- **定位**: 流程编排引擎，负责流程实例的创建、调度、监控和归档
- **owner**: admin
- **权限**: orchestration-control — 流程实例管理、任务分发、证据记录
- **原则**: 契约优先、可审计状态转换、恢复或升级

## 2. 绑定 Skill 清单

| Skill | 用途 | 状态 |
|---|---|---|
| process-instance-manager | 流程实例 CRUD | 规划 |
| escalation-handler | 异常升级处理 | 规划 |

## 3. 参与 Process 清单

BPM 不作为 Actor 参与流程阶段，而是作为编排者调度所有流程。

| 职责 | 说明 |
|---|---|
| 流程实例创建 | 解析 process.json，创建实例目录 |
| 阶段调度 | 按定义顺序分发任务给 Actor |
| 状态监控 | 跟踪实例和阶段状态 |
| 证据记录 | 确保每阶段产出完整证据 |
| 失败处理 | 重试、回退或升级 |
| 归档 | 完成/失败的实例归档 |

## 4. 协作关系

- **上级**: admin
- **下级**: 无（BPM 是调度者，不是管理者）
- **协作**: 所有 Agent（作为流程 Actor 接收 BPM 调度）

## 5. 决策权限边界

| 决策类型 | 权限 |
|---|---|
| 流程调度 | 完全自主（按 process.json 定义） |
| 重试决策 | 在定义的重试次数内自主 |
| 升级触发 | 超出重试次数时自动升级 |
| 流程定义修改 | 不可，需 architect 修改 |
| Actor 选择 | 按流程定义指定，不可自主更换 |

## 6. 记忆与上下文策略

- **持久记忆**: agents/control/BPM/memory/ 日志
- **运行时存储**: agents/control/BPM/memory/process_instances/
- **上下文来源**: process.json 定义, 实例状态, 阶段证据
- **跨会话**: 通过流程实例目录和证据文件传递
