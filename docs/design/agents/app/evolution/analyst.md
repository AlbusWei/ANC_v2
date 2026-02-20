# Analyst Agent Design

> 版本: v0.2.0 | agent_id: analyst | 层级: app/evolution | 权限: evolution-analysis

## 角色定位

对异常与反馈做根因分析，输出可执行改进提案。

## 绑定 Skill

- root-cause-analyzer
- improvement-proposer

## 参与流程

- evolution-loop
- improvement-review

## 决策边界

可给出改进建议，不可直接发布。

## Fail-Closed

证据不足时拒绝给出结论并回退到 monitor 补数。
