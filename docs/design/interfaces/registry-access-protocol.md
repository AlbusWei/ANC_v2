# Registry 读写协议

> 版本: v0.1.0 | SSOT 上游: [registry_contracts.md](../../architecture/registry_contracts.md)

## 概述

定义对三表注册中心（agent_directory, skill_registry, process_registry）的读写规则。

## 读取协议

### 谁可以读

所有 Agent 可读取所有 Registry 数据。Registry 是公开的资产目录。

### 读取方式

直接读取 JSON 文件: `shared/registry/{registry_name}.json`

### 缓存策略

不缓存。每次需要时直接读取文件，确保获取最新状态。

## 写入协议

### 谁可以写

| Registry | 写入权限 |
|---|---|
| agent_directory.json | admin, hr |
| skill_registry.json | hr, architect (新建时) |
| process_registry.json | hr, bpm (新建时) |

### 写入流程

1. **校验**: 使用 registry-validator 校验变更合法性
2. **备份**: 写入前保存当前版本（可选，Phase 2+）
3. **写入**: 更新 JSON 文件
4. **验证**: 写入后再次校验一致性
5. **同步**: 更新对应 inventory 文档

### 写入约束

- 不可删除 active 状态的条目（必须先 deprecated → retired）
- 不可修改 agent_id/skill_id/process_id（不可变标识）
- version 变更必须遵循 SemVer
- status 变更必须遵循生命周期状态机

## 错误处理

| 错误 | 处理 |
|---|---|
| JSON 语法错误 | 拒绝写入，报告错误位置 |
| 路径不存在 | 拒绝写入，报告缺失路径 |
| 名称不一致 | 拒绝写入，报告不一致字段 |
| 权限不足 | 拒绝写入，建议升级 |
| 并发冲突 | 后写入者需重新读取并合并 |

## OpenClaw 同步

Registry 变更后，如涉及 OpenClaw 配置映射：
1. 更新 `config/openclaw.*.json` 对应条目
2. 通过 `openclaw gateway call config.patch` 热更新
3. 需要重启的变更（gateway/discovery）需人工确认
