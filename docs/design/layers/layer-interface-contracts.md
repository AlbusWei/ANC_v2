# 层间接口契约

> 版本: v0.2.0 | SSOT 上游: [system_overview.md](../../architecture/system_overview.md) §六层架构

## 总则

- 上层依赖下层，下层不得反向依赖上层
- 所有跨层调用必须通过定义的接口，不得绕过
- 接口变更需 architect 审批并同步更新本文档
- App 层请求不得直达 admin，必须通过 BPM 门禁和升级链路

## 契约 1: L1 调用 L0（能力消费基础设施）

| 接口 | 方向 | 协议 | 说明 |
|---|---|---|---|
| Agent 执行 | L1 调用 L0 | `openclaw agent execute` | 启动 Agent 会话 |
| 配置管理 | L1 调用 L0 | `openclaw gateway call config.*` | 读写运行时配置 |
| LLM 推理 | L1 调用 L0 | LLM Provider API | 大模型推理 |
| 文件读写 | L1 调用 L0 | POSIX FS | 持久化 |

**Fail-Closed**: L0 不可用时，L1 所有 Skill 执行失败并记录错误。

## 契约 2: L1 → L2（能力 → 编排治理）

| 接口 | 方向 | 协议 | 说明 |
|---|---|---|---|
| Skill 调用 | L2 调用 L1 | BPM dispatch → Actor.execute(Skill) | BPM 调度 Actor 执行 Skill |
| Skill 发现 | L2 查询 L1 | skill_registry.json 读取 | 查找可用 Skill |
| 执行结果 | L1 返回 L2 | 结构化 Output + 证据文件 | Skill 执行结果 |

**Fail-Closed**: Skill 执行失败时，BPM 记录失败证据，触发重试或升级。

## 契约 3: L3 请求 L2（自开发消费编排治理）

| 接口 | 方向 | 协议 | 说明 |
|---|---|---|---|
| 流程启动 | L3 提交 L2 | process 定义 + input | 提交开发流程 |
| 任务调度 | L2 调度 L3 | BPM task dispatch | 分配阶段任务给 Actor |
| 状态反馈 | L2 返回 L3 | instance status query | 流程实例状态 |
| 生命周期 | L3 请求 L2 | lifecycle transition request | 新资产注册/状态转换 |

**Fail-Closed**: 因果驱动链任一阶段失败，BPM 阻止后续阶段。

## 契约 3.1: L3/L4/L5 触发入口到 L2（Trigger/Hook Ingress）

| 接口 | 方向 | 协议 | 说明 |
|---|---|---|---|
| 定时触发 | L3/L4/L5 提交 L2 | schedule trigger request | 定时触发请求进入 BPM |
| 事件触发 | L3/L4/L5 提交 L2 | canonical event envelope | 外部事件先标准化再匹配 |
| 幂等去重 | L2 内部执行 | dedupe ledger check | 优先 `event_id`，缺失回退业务键 |
| 触发审计 | L2 返回调用方 | trigger receipt + evidence_ref | 记录触发命中/拒绝/补跑结果 |

**Fail-Closed**:
1. 事件缺少最小字段或证据引用不可达时拒绝触发。
2. 风险级别无法判定时按高风险升级 admin。
3. 高风险系统写操作必须由 admin 执行，BPM 不得代执行。

## 契约 4: L4 与 L3（演化调度与开发反馈）

| 接口 | 方向 | 协议 | 说明 |
|---|---|---|---|
| 改进任务 | L4 下发 L3 | improvement proposal → dev task | 演化决策转开发任务 |
| 开发反馈 | L3 返回 L4 | dev result + evidence | 开发结果与证据 |
| 指标采集 | L4 从 L3 采集 | metric query | 开发效率等指标 |

**Fail-Closed**: 改进任务开发失败时，L4 记录失败并回滚改进提案状态。

## 契约 5: L5 与 L4（业务反馈与演化回流）

| 接口 | 方向 | 协议 | 说明 |
|---|---|---|---|
| 能力交付 | L4 向 L5 | 新/改进的业务能力 | 演化产出的业务能力 |
| 业务指标 | L5 向 L4 | metric report | 业务运行指标反馈 |
| 需求反馈 | L5 向 L4 | improvement request | 业务层改进需求 |

**Fail-Closed**: Phase 3+ 定义具体失败处理策略。

## 依赖方向校验

```
L5 Business ──依赖──> L4 Evolution ──依赖──> L3 Self-Dev ──依赖──> L2 Orchestration ──依赖──> L1 Capability ──依赖──> L0 Infrastructure
```

- 禁止反向依赖（如 L0 调用 L1 的 Skill）
- 禁止跨层直接调用（如 L3 直接调用 L0，必须经过 L1/L2）
- 同层内组件可直接交互（如 L2 的 BPM 与 HR）
