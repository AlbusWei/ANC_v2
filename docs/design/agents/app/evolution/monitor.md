# Monitor Agent Design

> 版本: v0.2.0 | agent_id: monitor | 层级: app/evolution | 权限: evolution-observability

## 角色定位

采集系统运行指标并触发异常检测，是自演化闭环入口。

## 绑定 Skill

- metric-collector
- anomaly-detector

## 参与流程

- evolution-loop
- health-check

## 决策边界

可发起异常告警，不可直接修改资产。

## Fail-Closed

指标缺失或采集失败时上报 analyst 与 bpm。
