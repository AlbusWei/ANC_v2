# L0 — 基础设施层详细设计

> 版本: v0.1.0 | SSOT 上游: [system_overview.md](../../architecture/system_overview.md) §六层架构

## 1. 层级定位

- **职责**: 提供 Agent 运行时环境、LLM 网关、文件系统、配置管理等基础能力
- **上层消费者**: L1 Capability（所有 Agent 运行依赖本层）
- **下层依赖**: 无（最底层）
- **核心原则**: 本层由外部平台（OpenClaw）提供，ANC v2 通过配置和接口契约消费

## 2. 组件清单

| 组件 | 类型 | 提供方 | 说明 |
|---|---|---|---|
| OpenClaw Gateway | 运行时 | 外部 | Agent 执行网关，提供 CLI/RPC |
| LLM Provider | 服务 | 外部 | 大语言模型推理服务 |
| File System | 基础设施 | OS | 文档/证据/注册表持久化 |
| OpenClaw Config | 配置 | ANC v2 | 运行时配置片段 |

## 3. 本层 Agent

无。L0 不包含 ANC v2 自有 Agent。

## 4. 本层 Skill

无。L0 能力由外部平台原生提供。

## 5. 本层 Process

无。

## 6. 接口契约

### 向上暴露（供 L1 消费）

| 接口 | 协议 | 说明 |
|---|---|---|
| Agent 执行 | `openclaw agent execute` CLI | 启动 Agent 会话 |
| 配置管理 | `openclaw gateway call config.*` RPC | 读写运行时配置 |
| 健康检查 | `openclaw health` CLI | 网关/Agent 健康状态 |
| 文件读写 | POSIX FS | 文档、注册表、证据链持久化 |

### 向下消费

无。

## 7. 约束与风险

- OpenClaw 版本升级可能破坏接口兼容性 → 锁定接口版本，变更需 architect 评审
- LLM Provider 不可用时全系统停摆 → 需要 Fail-Closed 降级策略
- 文件系统并发写入冲突 → 单 Actor 单任务原则天然规避

## 8. 验收标准

- [ ] OpenClaw Gateway 可正常启动并响应 health 检查
- [ ] Config RPC 可读写配置片段
- [ ] Agent execute 可启动至少一个 kernel Agent 会话
- [ ] 文件系统路径约定与 registry 一致
