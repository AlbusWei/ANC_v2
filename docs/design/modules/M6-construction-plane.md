# M6 — 施工面模块详细设计

> 版本: v0.1.0 | 建设优先级: P0（最先建设）| SSOT 上游: [system_overview.md](../../architecture/system_overview.md)

## 1. 模块定位

施工面（Construction Plane）是系统建设过程的可视化看板和进度追踪中心。它不是运行时组件，而是建设期的协调工具。

## 2. 组件分解

| 组件 | 类型 | 状态 | 说明 |
|---|---|---|---|
| construction_plane.md | 文档 | active | 实时施工看板 |
| ADR 记录 | 文档节 | active | 架构决策记录 |
| 里程碑追踪 | 文档节 | active | M0-M4 里程碑状态 |
| 风险登记 | 文档节 | active | 开放风险与缓解措施 |
| 开放问题 | 文档节 | active | 待决问题追踪 |

## 3. 所需 Agent/Skill/Process

- **Agent**: admin（施工面维护者）, architect（ADR 记录者）
- **Skill**: 无专属 Skill（手动维护）
- **Process**: 无专属 Process

## 4. 依赖关系

- 被所有其他模块依赖（提供建设进度上下文）
- 不依赖任何运行时模块

## 5. 数据模型

施工面为非结构化 Markdown，关键节包含：
- 里程碑表格: `| 编号 | 名称 | 状态 | 完成条件 |`
- ADR 条目: `ADR-{NNN}: {标题} — {决策} (日期)`
- 风险条目: `R-{NNN}: {描述} → {缓解}`

## 6. 验收标准

- [x] construction_plane.md 已创建并包含完整结构
- [x] Phase 0/0.5 里程碑已记录
- [x] ADR 1-5 已记录
- [ ] 每次重大推进后及时更新
