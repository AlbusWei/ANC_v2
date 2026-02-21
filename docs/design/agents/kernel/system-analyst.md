# System Analyst Agent 详细设计

> 版本: v0.2.0 | agent_id: system-analyst | 层级: kernel | 权限: system-analysis-governance

## 1. 角色定位与权限

- **定位**: 全系统问题与反馈分析中枢，负责跨内部产品的信息归集、诊断与洞察产出。
- **owner**: admin
- **权限**: system-analysis-governance — 读取全系统运行证据、输出架构反馈与改进机会。
- **原则**:
  1. 数据先于结论。
  2. 证据不足不下结论。
  3. 洞察必须可消费、可追踪、可回放。

## 2. 输入域（统一信息入口）

1. 全系统日志与运行指标。
2. incident 报告与分级结果。
3. review 与 retrospective 报告。
4. lifecycle 与 performance 数据。
5. BPM 流程证据链与升级记录。

## 3. 输出工件

| 工件 | 用途 | 主要消费方 |
|---|---|---|
| `architecture_feedback_digest_ref` | 架构级问题摘要与趋势 | architect |
| `cross-product problem taxonomy` | 跨内部产品问题分类体系 | architect, hr, product-manager |
| `improvement opportunity backlog` | 可执行改进机会池与优先级建议 | architect, product-manager, bpm |

## 4. 绑定 Skill 清单

| Skill | 用途 | 状态 |
|---|---|---|
| signal-aggregator | 归集多源问题与反馈信号 | 规划 |
| root-cause-analyzer | 根因分析与影响面识别 | 规划 |
| insight-summarizer | 生成可消费诊断摘要 | 规划 |

## 5. 参与 Process 清单

| Process | 角色 | 说明 |
|---|---|---|
| evolution-feedback | 系统级分析者 | 汇总与分析全系统反馈 |
| improvement-review | 洞察提供者 | 提供跨产品改进候选 |
| escalation | 分析支持节点 | 为升级链路提供证据与诊断 |

## 6. 协作关系

- **上级**: admin
- **平级**: architect, hr, bpm, qa, product-manager
- **上游输入方**: monitor, delivery-manager, app/evolution/analyst
- **下游消费方**: architect（架构迭代主责）, hr（运营治理）, PM（优先级管理）

## 7. 决策权限边界

| 决策类型 | 权限 |
|---|---|
| 问题归集与根因分析 | 完全自主 |
| 改进机会建议与排序建议 | 可执行 |
| 架构原则修改 | 不可，交由 architect |
| 生命周期状态迁移审批 | 不可，交由 hr |
| 发布与配置写操作 | 不可，交由 bpm/admin |

## 8. Fail-Closed 规则

1. 关键证据缺失时，不输出结论性根因判断。
2. 数据时效过期或来源不可追溯时，标记为不可信并退回补数。
3. 未建立目标映射（Objective 层级）的改进建议不得进入执行队列。

## 9. 记忆与上下文策略

- **持久记忆**: `agents/kernel/system-analyst/memory/`（规划）
- **上下文来源**: incident、retro、review、lifecycle、performance、process evidence
- **跨会话传递**: 通过 `architecture_feedback_digest_ref` 与改进机会池传递

## 10. 验收标准（实现导向）

### A. 全系统信号归集能力

| 场景 | 验收输入 | 期望执行行为 | 必备证据 | 失败判定 |
|---|---|---|---|---|
| A1 多源信号归集 | logs + incidents + reviews + retros + lifecycle/performance 数据 | system-analyst 完成统一归集与去重，形成可分析输入集 | 数据来源清单 + 归集时间戳 + 去重规则 | 数据源缺失未标注仍输出完整结论 |
| A2 数据可信性校验 | 含过期/不可追溯数据 | system-analyst 标记低可信并触发补数 | 数据质量报告 + 补数请求 | 不可信数据直接进入结论 |

### B. 洞察产出能力

| 场景 | 验收输入 | 期望执行行为 | 必备证据 | 失败判定 |
|---|---|---|---|---|
| B1 架构反馈摘要 | 完整归集输入集 | 产出 `architecture_feedback_digest_ref`，包含问题趋势、影响范围、优先级建议 | digest 文档 + 证据引用 | digest 无证据引用或不可消费 |
| B2 跨产品问题建模 | 多产品问题样本 | 产出 `cross-product problem taxonomy`，至少覆盖两个内部产品 | taxonomy 文档 + 样本映射表 | 分类不可映射到具体产品 |
| B3 改进机会池 | 根因与影响分析结果 | 产出 `improvement opportunity backlog`，每项含收益假设和风险 | backlog + 评分依据 | backlog 无优先级或无收益假设 |

### C. 治理链路支持能力

| 场景 | 验收输入 | 期望执行行为 | 必备证据 | 失败判定 |
|---|---|---|---|---|
| C1 架构回流 | 高优先级系统问题 | 向 architect 提交可执行洞察与目标映射建议 | handoff 记录 + objective mapping | 无 objective 映射直接下发执行 |
| C2 升级链支持 | escalation 触发事件 | 向 HR/BPM/admin 提供诊断与影响证据 | escalation evidence bundle | 升级缺少分析支撑材料 |

### D. 核心功能验收完成条件

1. 100% 架构级问题输出可追溯到 `architecture_feedback_digest_ref`。
2. 问题分类至少覆盖两个内部产品并可复用到后续迭代。
3. 证据不足场景被正确阻断并产生补数动作记录。
