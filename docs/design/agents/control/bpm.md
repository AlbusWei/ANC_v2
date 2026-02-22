# BPM Agent 详细设计

> 版本: v0.3.0 | agent_id: bpm | 层级: control | 权限: orchestration-control

## 1. 角色定位与权限

- **定位**: 流程编排引擎，负责流程实例创建、调度、监控、归档与治理门禁
- **owner**: admin
- **权限**: orchestration-control — 流程实例管理、任务分发、证据记录、审批门禁执行
- **原则**: 契约优先、状态可审计、证据先于推进、恢复或升级

## 2. 绑定 Skill 清单

| Skill | 用途 | 状态 |
|---|---|---|
| process-instance-manager | 流程实例 CRUD + 会话隔离治理 | review |
| trigger-ingress-normalizer | 触发入口归一（schedule/event） | draft（可执行，runner 已落盘） |
| trigger-matcher-dedupe | 规则命中与幂等去重 | draft（可执行，runner 已落盘） |
| evidence-recorder | trigger/instance 双向追溯证据归档 | draft（可执行，runner 已落盘） |
| catchup-scheduler | 动态补跑窗口决策 | draft（可执行，runner 已落盘） |
| escalation-handler | 异常升级处理 | draft（可执行，runner 已落盘） |
| config-change-gatekeeper | 配置变更门禁校验 | draft（可执行，runner 已落盘） |

## 3. 参与 Process 清单

BPM 不作为 Actor 参与业务阶段，而是作为编排者调度所有流程。

| 职责 | 说明 |
|---|---|
| 流程实例创建 | 解析 `process.json`，创建实例目录 |
| 会话隔离绑定 | 为实例写入 `session_binding.json` 并强制 `--session-id` 调度 |
| 阶段调度 | 按定义顺序分发任务给 Actor |
| 状态监控 | 跟踪实例和阶段状态 |
| 证据记录 | 确保每阶段产出完整证据 |
| Trigger Runtime 执行 | 执行 `trigger-schedule-runtime` / `trigger-event-runtime` runner 并落盘 TG 证据 |
| 配置变更门禁 | 对系统配置改动执行审批、分级和执行路径选择 |
| 失败处理 | 重试、回退或升级 |
| 归档 | 完成/失败实例归档 |

## 4. 协作关系

- **上级**: admin
- **下级**: 无（BPM 是调度者，不是管理者）
- **协作**: 所有 Agent（作为流程 Actor 接收 BPM 调度）
- **入口协作**: personal-assistant（默认人类请求入口）

## 5. 决策权限边界

| 决策类型 | 权限 |
|---|---|
| 流程调度 | 完全自主（按 `process.json` 定义） |
| 重试决策 | 在定义重试次数内自主 |
| 升级触发 | 超出重试次数时自动升级 |
| 配置变更风险分级 | 可执行（low/medium/high） |
| 高风险配置写操作执行者选择 | 固定为 admin，不可替换 |
| 流程定义修改 | 不可，需 architect 修改 |
| Actor 选择 | 按流程定义指定，不可自主更换 |

## 6. OpenClaw 配置变更编排协议

1. 接收请求：来自 app/kernel/human 入口，统一转为 `config_change_request`。
2. 校验门禁：必须包含 `objective/spec/test`、影响范围、回滚方案、期望证据。
3. 风险分级：按全局影响面和可逆性划分 `low/medium/high`。
4. 执行路径选择：
   - App 层请求：必须走 `BPM -> admin`。
   - Kernel 层请求：仅白名单幂等低风险变更可直达执行者，仍需 BPM 留痕。
   - 其他情况：升级到 admin 决策。
5. 执行回执：收集执行前后 hash、补丁摘要、验证结果、回滚状态。
6. 归档闭环：将证据写回实例目录并通知请求方。

## 7. Fail-Closed 行为

1. 请求字段不完整或证据缺失时拒绝调度。
2. 无法判定风险级别时按高风险处理并升级 admin。
3. 执行回执不完整时阻止流程推进并标记失败。

## 8. 记忆与上下文策略

- **持久记忆**: `agents/control/BPM/memory/` 日志
- **运行时存储**: `agents/control/BPM/memory/process_instances/`
- **上下文来源**: `process.json` 定义、实例状态、阶段证据、配置变更回执
- **跨会话**: 通过流程实例目录和证据文件传递

## 9. W3 运行级入口

1. `processes/control/trigger-schedule-runtime/scripts/trigger_schedule_runtime_runner.py`
2. `processes/control/trigger-event-runtime/scripts/trigger_event_runtime_runner.py`
3. `tests/m2-bpm-runtime/run_tc_tg.py`（TG-SCH/TG-EVT 全套回归入口）
