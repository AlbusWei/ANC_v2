# Role Handoff Protocol

> 版本: v0.2.0

## 目标

规范跨职能 Agent 的任务交接，避免隐式上下文和责任漂移。

## 交接最小字段

1. `handoff_id`
2. `from_role`
3. `to_role`
4. `objective_ref`
5. `input_ref`
6. `output_contract`
7. `acceptance_criteria`
8. `deadline`
9. `risk_notes`
10. `evidence_ref`

## 协议流程

1. 发送方提交交接包。
2. 接收方校验输入与目标。
3. 校验失败则拒收并返回缺失项。
4. 执行后回传 `completion` 包。

## Fail-Closed

1. 关键信息缺失：拒收。
2. 证据不可达：拒绝流转。
3. 超时：触发 escalation。
