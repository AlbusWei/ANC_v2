# ANC v2 上下文协议（Context Protocol）

最后更新：2026-02-18  
版本：2.0.0-alpha

> 本文档定义跨 Agent 上下文如何传递、落盘、追溯和回写。

## 1. 核心原则

1. 文档是跨 Agent 上下文的唯一持久载体。
2. 会话记忆只用于当前交互，不作为跨流程事实来源。
3. 未落盘信息视为不存在。

## 2. 文档化传递模型

标准交接链：

`Phase Output -> 落盘文档 -> BPM 摘要 -> Next Phase Input`

要求：

1. 每个 Phase 产出必须有路径引用。
2. 引用路径优先使用绝对路径。
3. 关键结论必须有 `evidence_ref`。

OpenClaw 运行态辅助接口：

1. `openclaw sessions --json`：查询会话索引。
2. `openclaw session show <session-id>`：查看单会话内容用于核对上下文漂移。

## 3. 文件与命名约定

建议命名：

1. `context.md`：流程上下文主文档。
2. `input.md`/`output.md`：阶段输入输出快照。
3. `decision.md`：关键决策记录。
4. `state.json`：结构化状态机。

命名建议：`<phase-id>_<artifact-type>_<timestamp>`。

## 4. 交接最小字段

跨 Phase 交接至少包含：

1. `objective_ref`
2. `phase_id`
3. `input_ref`
4. `output_ref`
5. `acceptance_criteria`
6. `known_risks`
7. `next_actions`

## 5. 大上下文处理

1. 先生成摘要，再链接原始文档。
2. 摘要不得改写原文含义。
3. 超长文档应分块并提供索引。

## 6. 变更回写规则

1. 架构变更 -> 更新 `system_overview.md`。
2. 流程规则变更 -> 更新 `process_architecture.md`。
3. 资产变更 -> 更新对应 registry。
4. 阶段进展变更 -> 更新 `construction_plane.md`。

## 7. 协议违规处理

以下情况视为协议违规：

1. 仅在会话中传达关键结论但不落盘。
2. Phase 无法追溯输入来源。
3. 输出无路径或无证据锚点。
4. 修改资产但未更新 registry。

默认处理：

1. BPM 拒绝流转。
2. 回退到上一步补齐文档。
3. 记录违规事件。
