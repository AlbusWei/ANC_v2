## ADDED Requirements

### Requirement: Meta Asset Validation Must Execute Through QA Online Runtime Flows
Meta 资产验收 MUST 通过 QA 在线运行流执行，且以 openclaw runtime 行为为主判据。

#### Scenario: Online suite executes against openclaw runtime
- **WHEN** 执行 `tests/m3-self-development` 的 Meta 在线套件
- **THEN** 每个关键资产至少覆盖 Happy/Fail-Closed/Traceability 场景
- **AND** 输出可追溯证据索引

### Requirement: Online Runtime Failures Must Block Release And Trigger Defect-Closure Loop
在线用例失败 MUST 阻断阶段收口并触发缺陷闭环。

#### Scenario: Failed case creates defect and mandatory regression run
- **WHEN** 任一关键在线 case 失败
- **THEN** 必须生成缺陷记录并执行修复后回归
- **AND** 未回归通过前不得推进 phase 状态

### Requirement: Static Contract Checks Are Baseline Gates But Cannot Replace Runtime Acceptance
静态门禁可作为基础准入，但 MUST NOT 替代运行时主验收。

#### Scenario: Static-only success is rejected as insufficient evidence
- **WHEN** 仅提供 `registry verify` 和 `openspec validate` 通过结果
- **THEN** 应判定证据不足
- **AND** 要求补齐在线运行证据后再评审

### Requirement: QA Reports Must Provide Natural-Language Conclusions Instead Of Raw Logs Only
QA 报告 MUST 产出自然语言结论，不能只贴原始日志。

#### Scenario: Report includes objective, coverage, phenomena and risk judgement
- **WHEN** 在线执行结束
- **THEN** 报告必须包含测试目标、覆盖范围、关键现象、风险判断、准入结论
- **AND** 引用对应证据路径
