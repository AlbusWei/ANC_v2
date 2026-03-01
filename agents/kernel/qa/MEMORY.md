# QA - MEMORY

## Long-Term Memory

- Stable preferences:
  - 证据链优先于口头结论
  - 判定输出采用统一 verdict 契约
- Known constraints:
  - override 权限仅 admin 持有
  - AP-024/AP-025 由 bpm 主责
- Important historical decisions:
  - 2026-02-21: 单体 QA 模式成立（测试设计与判定同属 qa），但必须执行顺序冻结、证据闭环、争议升级约束
  - 2026-02-21: AP-008 主观评测默认启用
  - 2026-02-21: P0 风险零漏判优先

## Update Rules

1. 只记录跨会话稳定信息。
2. 不记录临时执行细节（放到 `runtime_data/agent-memory/<agent-id>/YYYY-MM-DD.md`）。
3. 重大治理决策变化后必须同步更新。
