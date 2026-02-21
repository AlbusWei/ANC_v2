# Role Handoff Protocol

> 版本: v0.3.0 | SSOT 上游: `docs/architecture/process_architecture.md` + `docs/architecture/context_protocol.md`

## 目标

规范跨职能 Agent 的任务交接，避免隐式上下文和责任漂移。

## 对齐策略

采用“BPM/Context 子集 + 业务补充”模型：

1. 继承 `instance/lineage/phase/objective/input/output` 关键字段。
2. 保留 `from_role/to_role/deadline/risk_notes` 等业务字段。

## 交接最小字段

1. `instance_id`
2. `parent_instance_id`（递归场景必填）
3. `lineage_ref`
4. `stack_depth`
5. `phase_id`
6. `objective_ref`
7. `input_ref`
8. `output_ref`
9. `output_contract`
10. `from_role`
11. `to_role`
12. `acceptance_criteria`
13. `deadline`
14. `risk_notes`
15. `evidence_ref`

## 协议流程

1. 发送方提交交接包。
2. 接收方校验输入、lineage 和目标。
3. 校验失败则拒收并返回缺失项。
4. 执行后回传 `completion` 包。

## Fail-Closed

1. 关键信息缺失：拒收。
2. `stack_depth` 与 lineage 不一致：拒绝流转。
3. 证据不可达：拒绝流转。
4. 超时：触发 escalation。
