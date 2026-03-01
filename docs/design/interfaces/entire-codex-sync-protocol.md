# Entire x Codex 同步协议

> 状态: draft | 目标: 在无官方 Codex 集成的前提下，为 ANC v2 提供可审计的 Entire 会话同步路径。

## 1. 场景

1. 使用 Codex 进行实现，但需要 Entire 生成 checkpoint 与会话证据。
2. 需要在每次开发变更后主动同步，而非仅在最终提交时补录。
3. **仅限 Codex 运行时**：若在 Claude Code 运行时调用本桥接，会把会话错误标记为 Gemini；Claude Code 应走 `entire hooks claude-code ...` 原生路径。

## 2. 协议入口

脚本：
`skills/system/entire-codex-sync/scripts/entire_codex_bridge.py`

命令：

1. `start`：创建/复用桥接会话。
2. `sync`：驱动 `session` 的一个开发回合（before-agent + after-agent）。
3. `status`：输出会话可观测状态。
4. `end`：结束会话。

## 3. Entire 生命周期映射

桥接脚本调用以下内部命令（Gemini hook 兼容路径）：

1. `entire hooks gemini session-start`
2. `entire hooks gemini before-agent`
3. `entire hooks gemini after-agent`
4. `entire hooks gemini session-end`

## 4. 证据与输出

1. 提交消息 trailer：`Entire-Checkpoint: <id>`
2. 会话状态：`.entire/codex-bridge/session.json`
3. 会话转录：`.entire/codex-bridge/transcript.json`

## 5. Fail-Closed 规则

1. 非 Git 仓库：失败。
2. Entire 未启用或 CLI 不可用：失败。
3. Hook 调用返回非零：失败。
4. 状态/转录 JSON 无法解析：失败。

## 6. 使用约束

1. 每个开发回合（有代码变更）都执行一次 `sync`。
2. 每次 `git commit` 后检查 `Entire-Checkpoint` trailer。
3. 会话结束后执行 `end`，避免状态泄漏到下一个任务。
