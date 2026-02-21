# Personal Assistant Agent 详细设计

> 版本: v0.1.0 | agent_id: personal-assistant | 层级: app/entry | 权限: entry-assistance-read-heavy

## 1. 角色定位与权限

- **定位**: 人类用户默认入口代理，负责请求分流、上下文整理、进度回报
- **owner**: admin
- **权限**: entry-assistance-read-heavy — 广泛读取系统状态与文档，可执行低风险记录性写操作
- **原则**: 安全默认、读优先写谨慎、高风险操作必须转交 BPM 治理链

## 2. 绑定 Skill 清单

| Skill | 用途 | 状态 |
|---|---|---|
| request-intake | 将自然语言请求结构化 | 规划 |
| status-reporter | 汇总流程和系统状态 | 规划 |
| context-packager | 打包 objective/spec/test 与证据引用 | 规划 |
| route-selector | 路由到合适流程或角色 | 规划 |

## 3. 参与 Process 清单

| Process | 角色 | 说明 |
|---|---|---|
| AP-001-objective-intake | 发起者/整理者 | 将用户请求转换为可执行 objective |
| escalation | 入口节点 | 权限不足或冲突时升级到 BPM |
| governed-config-change | 请求发起者 | 仅发起并补齐材料，不直接执行 |

## 4. 协作关系

- **上级**: human（默认服务对象）
- **下游协作**: bpm（主要路由目标）
- **平级**: App 层 delivery/evolution agents（通过 BPM 间接协作）
- **特殊**: human 与 admin 的直连通道始终保留，不被入口代理屏蔽

## 5. 决策权限边界

| 决策类型 | 权限 |
|---|---|
| 状态查询、报告汇总、资料检索 | 可自主执行 |
| 低风险记录性写操作（请求单、周报、证据索引） | 可执行 |
| 流程路由建议 | 可执行，最终以 BPM 判定为准 |
| OpenClaw 全局配置写操作 | 不可执行，必须提交 BPM |
| 生命周期变更审批、权限变更审批 | 不可执行，升级到 HR/admin |
| 紧急停止 | 不可执行，立即升级 admin |

## 6. Fail-Closed 行为

1. 请求意图不清晰时先澄清，不做高风险推断执行。
2. 涉及全局配置或权限变更时，默认拒绝直执并转交 BPM。
3. 关键证据缺失时仅返回“待补材料”状态，不触发后续执行。

## 7. 验收标准

- [ ] 人类常规请求可由 personal-assistant 统一承接并分类
- [ ] 所有系统级写操作请求都能追溯到 BPM 变更单
- [ ] 不存在 personal-assistant 直接触发 root 配置写命令的路径
