# Processes Directory

## Layout

1. `processes/template/`：流程模板资产。
2. `processes/meta/development-process/`：真实示例流程（canonical 路径）。
3. `processes/meta/governed-config-change/`：配置变更治理流程（canonical 路径）。
4. `processes/control/trigger-schedule-runtime/`：定时/心跳触发运行时流程（canonical 路径）。
5. `processes/control/trigger-event-runtime/`：事件触发运行时流程（canonical 路径）。
6. `processes/development-process/`：Phase 0.5 legacy 参考路径，不再作为 registry 真相源。

## Rule

- 每个 process 目录至少包含 `SKILL.md` 与 `process.json`。
- `template` 目录不注册到 registry。
- 非模板流程必须在 `process_registry.json` 可发现。
- `development-process` 仅以 `processes/meta/development-process` 注册； `development-process` 目录下的资产仅作为legacy参考，后续`processes/meta/development-process` 完善后将删除。
