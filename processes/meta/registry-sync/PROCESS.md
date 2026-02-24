# registry-sync - 流程说明

## 流程定位

- 流程级别：`P6`
- 负责人：`hr`
- 版本：`0.1.0`
- Objective 引用：`obj-m3-registry-sync-runtime`

## 流程目标（自然语言）

该流程用于 registry 一致性校验与同步落盘，确保资产状态迁移后目录与索引保持同源。它承担“系统目录真相维护”职责，是生命周期收口的必要环节。

## 协作编排原则

1. 该流程专注目录真相维护，确保资产状态与 registry 索引一致。
2. 同步前必须先完成 contract 校验，避免把错误状态写入系统索引。
3. 同步结果需具备审计可读性，明确改动对象与校验结论。
4. 该流程不承担生命周期决策，只承接已批准迁移的落盘收口。

## 阶段语义定义

### p1 verify-registry-and-sync

- 执行角色：`hr`
- 阶段目的：本阶段围绕以下业务动作推进：执行 registry 校验并落盘同步记录。
- 输入语义：本阶段主要消费以下输入：registry_patch 与 transition_request。
- 完成标准：完成判据：必须产出 registry_sync_ref + registry_verify_report_ref，并满足“registry 校验结果明确且可审计”。
- 交接说明：交接要求：将 registry_sync_ref + registry_verify_report_ref 交接给 initiator。
- 执行单元：`subprocess:inline-ap:registry-sync:p1`。该阶段采用临时 AP 语法，映射 skill 为 `sys.qa.registry-validator`，穿透执行策略：允许（同 Actor 场景）。

## 控制流与回退

- `p1` 在 `success` 条件下流转到 `end`。

## Fail-Closed 触发条件

1. 阶段输入不可解析、缺失或与目标语义不一致。
2. 阶段输出不可追溯，或无法支撑下一阶段继续执行。
3. 交接语义不完整，导致跨角色协作中断。
4. 回退/重试按策略执行：max_attempts=1。
