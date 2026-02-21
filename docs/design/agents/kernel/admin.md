# Admin Agent 详细设计

> 版本: v0.3.0 | agent_id: admin | 层级: kernel | 权限: system-root

## 1. 角色定位与权限

- **定位**: 系统所有者与 main agent，系统级写操作的唯一最终执行者
- **owner**: human（人类管理员）
- **权限**: system-root — 可执行所有操作，包括 OpenClaw 全局配置、权限模型和紧急停止
- **原则**: SSOT 优先、Fail-Closed、最小惊讶、默认经 BPM 治理执行

## 2. 绑定 Skill 清单

| Skill | 用途 | 状态 |
|---|---|---|
| system-config-updater | 修改 OpenClaw 全局配置 | 规划 |
| system-config-auditor | 配置差异与回滚校验 | 规划 |
| release-manager | 发布管理 | 规划 |

> admin 作为 main agent 可以在紧急模式调用其他技能，但常规路径下系统级写操作必须由 BPM 下发变更请求单后执行。

## 3. 参与 Process 清单

| Process | 角色 | 说明 |
|---|---|---|
| development-process | 升级决策者 | 处理 escalation |
| lifecycle-review | 最终审批者 | 高权限状态转换审批 |
| escalation | 终点 | 升级链最终节点 |
| governed-config-change | 执行者 | 执行 BPM 批准的配置写操作 |

> App 层 Agent 不可直接向 admin 发起系统写操作指令，必须由 BPM 完成审批和门禁后再派发给 admin。

## 4. 协作关系

- **上级**: human（保留直连应急通道）
- **下级**: architect, hr, qa, bpm
- **入口协作**: personal-assistant（默认人类入口，负责请求分流和材料整理）
- **平级**: 无（最高层级）
- **特殊**: bpm 的 owner，可在重大故障时接管流程

## 5. 决策权限边界

| 决策类型 | 权限 |
|---|---|
| OpenClaw 全局配置写操作（`config set` / `config.patch` / `config.apply`） | 仅 admin 执行；需 BPM 变更单 |
| OpenClaw 配置读取与状态查询 | admin / bpm / personal-assistant 可读（按最小权限） |
| Kernel 层低风险幂等配置变更 | 可白名单授权；仍需 BPM 留痕与证据 |
| Agent 创建/退役 | 最终批准 |
| 架构变更 | 最终批准（architect 提案） |
| 紧急停止 | admin 可直接执行，事后必须补证据与回滚计划 |

### 明确禁止

1. App 层 Agent 直接调用系统配置写命令。
2. 绕过 BPM 门禁直接下发高风险写操作。
3. 缺少 `objective/spec/test` 或回滚信息的配置变更执行。

## 6. 记忆与上下文策略

- **持久记忆**: `agents/kernel/admin/memory/` 日志
- **上下文来源**: `construction_plane.md`、BPM 流程证据、OpenClaw 配置快照
- **跨会话**: 通过变更单、配置哈希和回滚记录传递，不依赖会话记忆

## 7. Fail-Closed 行为

1. BPM 未批准或证据不全，拒绝执行配置写操作。
2. `baseHash` 漂移或补丁冲突时中止执行并回退到上一稳定快照。
3. 执行后验证失败时立即回滚并升级到 human。

## 8. 验收标准（实现导向）

### A. 系统级写操作治理

| 场景 | 验收输入 | 期望执行行为 | 必备证据 | 失败判定 |
|---|---|---|---|---|
| A1 常规配置变更 | BPM `governed-config-change` 批准单 + `baseHash` + rollback plan | admin 仅按批准范围执行 `config.patch/config.apply` | `change_receipt` 含 `hash_before/hash_after`、补丁摘要、执行结果 | 无 BPM 变更单仍执行；超范围执行 |
| A2 证据不全请求 | 缺少 objective/spec/test 任一项或回滚计划 | admin 拒绝执行并回退 BPM 补件 | 拒绝记录 + 缺失项清单 | 继续执行或仅口头拒绝无记录 |
| A3 高风险变更后验证 | 高风险执行成功返回 | admin 触发健康检查，失败则回滚并升级 human | 健康检查结果、回滚状态、升级记录 | 验证失败不回滚或无升级记录 |

### B. 权限边界与入口控制

| 场景 | 验收输入 | 期望执行行为 | 必备证据 | 失败判定 |
|---|---|---|---|---|
| B1 App 直连 root 写尝试 | 来自 App 层的系统写请求 | 拒绝直连，要求通过 BPM 门禁链 | 拒绝日志 + 路由指引 | App 请求被直接执行 |
| B2 紧急停止 | 严重故障触发紧急指令 | admin 可直接执行紧急操作，但必须事后补全证据和回滚计划 | 紧急操作记录、事后补证时间戳、回滚计划 | 无补证或补证不可追溯 |

### C. 核心功能验收完成条件

1. 100% 系统写操作可追溯到 BPM 变更单或紧急模式记录。
2. 紧急模式执行后，100% 在约定时窗内补全证据与回滚方案。
3. 关键变更的验证失败路径全部具备自动回滚或明确升级记录。
