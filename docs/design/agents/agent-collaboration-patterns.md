# Agent 协作拓扑

> 版本: v0.4.0

## 管理层级

```text
human
  ├── admin (直连应急通道)
  │     ├── system-analyst
  │     ├── architect
  │     │     └── kernel-dev
  │     ├── hr
  │     ├── qa
  │     └── bpm
  └── personal-assistant (默认入口)
        └── bpm (路由与治理门禁)
              └── app-layer delivery/evolution agents
```

## 协作模式

### 模式 0: 人类入口分流

`human -> personal-assistant -> bpm -> target actor`

`human -> admin` 直连路径始终保留，仅用于应急或最高权限指令。

### 模式 1: 内部产品孵化闭环（严格分工）

`signal-source -> architect -> hr -> qa -> kernel-dev -> qa -> hr -> release-manager-agent`

说明：

1. `signal-source` 可来自 business-analyst、product-manager 或 system-analyst。
2. architect 负责定义架构要求与审查，不直接创建非架构类 Agent 资产。
3. hr 作为 Agent 内部产品经理，负责资产文档与生命周期推进。

### 模式 2: 系统反馈治理闭环

`system feedback -> system-analyst -> architect -> hr/product-manager -> bpm`

说明：

1. system-analyst 统一归集全系统问题并产出 `architecture_feedback_digest_ref`。
2. architect 将洞察转为架构目标与治理要求。
3. hr 或 product-manager 接收需求并组织执行排期。
4. bpm 负责流程化执行与证据归档。

### 模式 3: 外部客户交付闭环

`business-analyst -> product-manager -> solution-architect -> tech-lead -> engineers -> qa-engineer -> delivery-manager -> customer-success-manager`

`delivery-iterations` 复用内部孵化闭环。

### 模式 4: 升级链

`actor -> owner -> bpm -> admin -> human`

### 模式 5: 元层自修改

`proposer -> architect -> qa -> admin -> kernel-dev -> qa -> hr`

## 通信规则

1. 跨 Agent 交互通过 BPM 调度或 role-handoff 协议。
2. 上下文必须文档化并包含 lineage 信息。
3. 无证据结论视为无效。
4. App 层不得直接触发系统级配置写操作，必须走 `BPM -> admin`。
5. 架构治理工件使用 `architecture_brd_ref`、`architecture_prd_ref`、`architecture_feedback_digest_ref`。
6. 模板共管决策必须记录 `template_change_dual_approval_record`。
