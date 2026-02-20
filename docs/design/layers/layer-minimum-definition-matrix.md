# Layer Minimum Definition Matrix

> 版本: v0.2.0 | 适用: L0-L5

## 规则

每一层至少定义七类对象：`Agents/Skills/Processes/Components/Interfaces/Data Models/Acceptance`。

| Layer | Agents | Skills | Processes | Components | Interfaces | Data Models | Acceptance |
|---|---|---|---|---|---|---|---|
| L0 Infrastructure | N/A | N/A | N/A | OpenClaw/Gateway/FS | CLI/RPC/FS | config/health snapshots | 可用性与兼容性验收 |
| L1 Capability | architect/kernel-dev/qa | meta/system skill 集 | 原子能力调用约束 | skill templates | Skill invoke & registry | skill schema | smoke + contract tests |
| L2 Orchestration | bpm/hr | lifecycle/permission/instance mgmt | governance/composite | BPM engine/store | BPM↔Actor, registry access | process/evidence schema | 编排与治理验收 |
| L3 Self-Development | architect/qa/kernel-dev/admin | dev/release/impact | full dev lifecycle | development pipeline assets | task handoff & gating | objective/spec/test artifacts | 端到端自开发验收 |
| L4 Self-Evolution | monitor/analyst/planner | metric/anomaly/prioritization | evolution loops | monitoring analyzers | improvement dispatch | metric/proposal schema | 改进前后对比验收 |
| L5 Business Delivery | delivery agents set | business skills | external delivery flows | delivery toolchain | client-facing + internal reuse | delivery contract schema | 客户验收与交付验收 |

## 检查条目

- [ ] 每层七类定义齐全
- [ ] 每层均声明 Fail-Closed 行为
- [ ] 层间接口方向符合 L5->L0 单向依赖
