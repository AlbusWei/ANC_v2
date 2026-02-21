# L1 — 能力层详细设计

> 版本: v0.2.0

## 层级定位

- 职责: 提供可复用原子能力（Skill）。
- 上层消费者: L2, L3。
- 下层依赖: L0。

## 最小定义（七类）

- Agents: architect, kernel-dev, qa
- Skills: meta + system skills
- Processes: 无流程编排，仅原子能力执行
- Components: skill templates, references, tests mount
- Interfaces: skill invoke, skill registry
- Data Models: skill schema, test schema
- Acceptance: smoke + contract gate

## 本层 Skill 清单

已有：llm-judge, spec-writer, test-designer, skill-creator

待建：objective-writer, agent-creator, process-creator, template-validator

## 约束

1. Skill 必须声明输入/输出契约。
2. Skill 必须声明 Fail-Closed。
3. active 前必须进入 review 并有测试挂载点。
