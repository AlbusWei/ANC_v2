# Trigger Governance 差异关闭计划（Round 1）

> 日期: 2026-02-21 | 范围: `codex/review-layers-modules` 文档治理收敛

## 1. 已关闭差异

1. M2/M4 边界与层间契约对齐  
引用：
`docs/design/layers/L2-orchestration-governance.md`  
`docs/design/modules/M2-bpm-engine.md`  
`docs/design/modules/M4-lifecycle-management.md`  
`docs/design/layers/layer-interface-contracts.md`

2. 触发治理路径写入模块依赖矩阵并挂验证锚点  
引用：
`docs/design/modules/module-dependency-matrix.md`

3. 最小 dry-run 证据路径落盘（TG-SCH-002 / TG-EVT-003）  
引用：
`docs/design/modules/evidence/trigger-governance/README.md`  
`docs/design/modules/evidence/trigger-governance/TG-SCH-002-dry-run.md`  
`docs/design/modules/evidence/trigger-governance/TG-EVT-003-dry-run.md`

## 2. 未关闭差异（进入下一轮）

1. 运行级证据仍缺失：TG-SCH-001/003/004、TG-EVT-001/002。  
Owner: bpm + qa  
退出条件：每条用例至少补一份运行级 evidence，回填 checklist。

2. trigger runtime 资产尚未执行化（当前为文档级治理）。  
Owner: bpm + architect  
退出条件：形成可执行流程与最小日志落盘策略。

## 3. 下一轮执行顺序（建议）

1. 先补运行级最小链路：`TG-EVT-003`（Fail-Closed）与 `TG-SCH-002`（heartbeat）回放。
2. 再补正向链路：`TG-EVT-001` 与 `TG-SCH-001`。
3. 最后补治理特例：`TG-EVT-002`（去重）与 `TG-SCH-003/004`（override/catchup）。
