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

4. trigger runtime 可执行资产已落盘（流程 + 技能 + AP）  
引用：
`docs/design/processes/trigger-schedule-runtime-process.md`  
`docs/design/processes/trigger-event-runtime-process.md`  
`docs/design/skills/bpm-runtime-skills.md`  
`processes/control/trigger-schedule-runtime/process.json`  
`processes/control/trigger-event-runtime/process.json`

5. `process-parser/scheduler/lineage-guard` 已决策并入 `sys.bpm.process-instance-manager` 子能力  
引用：
`docs/design/skills/bpm-runtime-skills.md`  
`skills/system/process-instance-manager/SKILL.md`  
`docs/design/standards/skill-definition-standard.md`

6. trigger runtime 收口策略已决策：当前保持双 P4 流程；如需收口，引入 P5 `trigger-runtime-supervisor` 模式  
引用：
`docs/design/modules/M2-bpm-engine.md`  
`docs/design/processes/trigger-runtime-supervisor-pattern.md`  
`docs/design/processes/p-levels/P5-subprocess-patterns.md`

## 2. 未关闭差异（进入下一轮）

1. 运行级证据仍缺失：TG-SCH-001/003/004、TG-EVT-001/002。  
Owner: bpm + qa  
退出条件：每条用例至少补一份运行级 evidence，回填 checklist。

2. 动态策略参数尚未完成运行级校准：`catchup_policy_ref` 与 `time_bucket_strategy` 仍缺实证回写。  
Owner: bpm + qa  
退出条件：至少完成一轮运行级回放并回写策略参数与命中统计。

## 3. 下一轮执行顺序（建议）

1. 先补运行级最小链路：`TG-EVT-003`（Fail-Closed）与 `TG-SCH-002`（heartbeat）回放。
2. 再补正向链路：`TG-EVT-001` 与 `TG-SCH-001`。
3. 最后补治理特例：`TG-EVT-002`（去重）与 `TG-SCH-003/004`（override/catchup）。
