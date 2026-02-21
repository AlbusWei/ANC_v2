# 治理流程清单与设计

> 版本: v0.5.0 | 分类: Governance Processes

## 核心治理流程

1. lifecycle-review
2. registry-sync
3. escalation
4. governed-config-change
5. hold-governance

## lifecycle-review

阶段：

1. validate-request
2. check-prerequisites
3. quality-gate
4. execute-transition
5. sync-registry

状态规则：`draft -> review -> active -> deprecated -> retired`

## escalation

升级链：`actor -> owner -> bpm -> admin -> human`

## governed-config-change

阶段：

1. intake-and-normalize（bpm）
2. gate-and-risk-classification（bpm）
3. authorize-change（admin）
4. execute-config-change（admin）
5. verify-and-archive（bpm）

约束：

1. 系统级配置写操作只能由 admin 执行。
2. 执行前必须完成 objective/spec/test 与 rollback 证据校验。
3. 执行后必须记录 hash_before/hash_after 与回滚状态。

## hold-governance

设计文档：`/Users/albus/MyProjects/ANC_v2/docs/design/processes/hold-governance-process.md`

阶段：

1. collect-progress-evidence（AP-021）
2. triage-and-classify（AP-022）
3. execute-triage-action（AP-023）
4. health-maintenance（AP-024）
5. close-or-escalate（AP-025）

关键约束：

1. 禁止以固定超时阈值直接判定失败。
2. triage 必须基于三类进展信号（日志增量/阶段推进/输出流心跳）。
3. triage 必须产出 `continue/retry/debug/fail` 之一。
4. 升级链固定为 `qa -> bpm -> admin`。

## Fail-Closed

1. 无权限或证据不足直接拒绝。
2. 状态迁移非法直接拒绝。
3. registry 不一致直接阻断。
4. 配置变更后健康检查失败且回滚失败时直接升级 human。
5. HOLD triage 无有效进展证据且无法补证时直接失败并升级。
