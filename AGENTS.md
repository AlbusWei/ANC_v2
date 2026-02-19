# ANC v2 - AGENTS

> 本文件是所有协作者（人类、外部 Coding Agent、系统内 Agent）进入项目的第一入口。

## 1. 项目目标

ANC v2 是一个可反身自开发、可自进化的 Agentic 系统。

## 2. SSOT 与核心文档

1. 架构 SSOT：`/Users/albus/MyProjects/ANC_v2/docs/architecture/system_overview.md`
2. 流程 SSOT：`/Users/albus/MyProjects/ANC_v2/docs/architecture/process_architecture.md`
3. 测试方法：`/Users/albus/MyProjects/ANC_v2/docs/architecture/test_methodology.md`
4. 上下文协议：`/Users/albus/MyProjects/ANC_v2/docs/architecture/context_protocol.md`
5. 施工平面：`/Users/albus/MyProjects/ANC_v2/docs/architecture/construction_plane.md`
6. 术语表：`/Users/albus/MyProjects/ANC_v2/docs/architecture/glossary.md`
7. OpenClaw 接口：`/Users/albus/MyProjects/ANC_v2/docs/architecture/openclaw_interface.md`
8. registry 契约：`/Users/albus/MyProjects/ANC_v2/docs/architecture/registry_contracts.md`

## 3. 执行原则

1. 因果驱动链：`Objective -> Spec -> Test -> Development`。
2. 冲突优先级：`Objective > Spec > Test > Implementation`。
3. 文档即真相：关键结论必须落盘。
4. Fail-Closed：证据不足或协议错误时默认失败并回退。
5. Skill/Process 必须遵循 Agent Skills 规范并与 OpenClaw 配置咬合。

## 4. 协作约束

1. 优先使用绝对路径引用。
2. 跨 Agent 上下文通过文档传递，不依赖会话记忆。
3. 变更架构/流程/资产后必须同步更新对应文档与 registry。
4. 未更新施工平面的推进不视为“已完成”。

## 5. OpenClaw 操作基线

1. 配置读取：`openclaw config get agents.list --json`
2. 配置补丁：`openclaw gateway call config.patch --params '{\"raw\":\"...\",\"baseHash\":\"...\"}' --json`
3. 网关健康检查：`openclaw health --json`
4. 会话检查：`openclaw sessions --json`
5. 代理执行：`openclaw agent --message \"...\"`

## 6. 当前阶段边界

当前处于 Phase 0/0.5：优先构建治理骨架，不做大规模业务功能实现。
