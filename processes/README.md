# Processes Directory

## Layout

1. `processes/template/`：流程模板资产。
2. `processes/meta/development-process/`：真实示例流程（canonical 路径）。
3. `processes/meta/full-development/`：M3 全链路自开发流程（canonical 路径）。
4. `processes/meta/hotfix/`：M3 紧急修复流程（canonical 路径）。
5. `processes/meta/refactor/`：M3 重构流程（canonical 路径）。
6. `processes/meta/governed-config-change/`：配置变更治理流程（canonical 路径）。
7. `processes/meta/construction-plane-governance/`：M6 施工联动治理流程（canonical 路径）。
8. `processes/control/trigger-schedule-runtime/`：定时/心跳触发运行时流程（canonical 路径）。
9. `processes/control/trigger-event-runtime/`：事件触发运行时流程（canonical 路径）。

## Rule

- 每个 process 目录至少包含 `SKILL.md` 与 `process.json`。
- `template` 目录不注册到 registry。
- 非模板流程必须在 `process_registry.json` 可发现。
- `development-process` 仅以 `processes/meta/development-process` 注册，历史 legacy 目录已退役移除。
