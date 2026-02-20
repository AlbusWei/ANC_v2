# L4 — 自演化层详细设计

> 版本: v0.2.0

## 层级定位

通过监控、分析、规划和改进驱动系统持续进化。

## 最小定义（七类）

- Agents: monitor, analyst, planner
- Skills: metric-collector, anomaly-detector, root-cause-analyzer, improvement-proposer, priority-ranker
- Processes: evolution-loop, health-check, improvement-review
- Components: metric store, proposal backlog
- Interfaces: evolution dispatch to L3
- Data Models: metric schema, proposal schema
- Acceptance: 改进前后指标可比较，失败可回滚

## 规则

1. 改进提案必须量化收益与风险。
2. 未通过回归测试不得进入发布。
3. 高风险改进需 admin 批准。
