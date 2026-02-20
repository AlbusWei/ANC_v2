# Agent 协作拓扑

> 版本: v0.2.0

## 管理层级

```text
human
  └── admin
        ├── architect
        │     └── kernel-dev
        ├── qa
        ├── hr
        ├── bpm
        └── app-layer delivery/evolution agents
```

## 协作模式

### 模式 1: 内部产品孵化闭环

`business-analyst -> architect -> qa -> kernel-dev -> qa -> hr -> release-manager-agent`

由 BPM 编排，遵循 Objective -> Spec -> Test -> Implement -> Verify -> Lifecycle -> Release。

### 模式 2: 外部客户交付闭环

`business-analyst -> product-manager -> solution-architect -> tech-lead -> engineers -> qa-engineer -> delivery-manager -> customer-success-manager`

`delivery-iterations` 复用内部孵化闭环。

### 模式 3: 升级链

`actor -> owner -> bpm -> admin -> human`

### 模式 4: 元层自修改

`proposer -> architect -> qa -> admin -> kernel-dev -> qa -> hr`

## 通信规则

1. 跨 Agent 交互通过 BPM 调度或 role-handoff 协议。
2. 上下文必须文档化并包含 lineage 信息。
3. 无证据结论视为无效。
