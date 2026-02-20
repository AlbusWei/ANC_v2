# Processes Directory

## Layout

1. `/Users/albus/MyProjects/ANC_v2/processes/template/`：流程模板资产。
2. `/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/`：运行时 SSOT 流程（Phase 1 基线）。
3. `/Users/albus/MyProjects/ANC_v2/processes/development-process/`：Phase 0.5 示例流程（归档示例，不作为运行基线）。

## Rule

- 每个 process 目录至少包含 `SKILL.md` 与 `process.json`。
- `template` 目录不注册到 registry。
- 运行时流程 SSOT 仅指向 `processes/meta/*`。
- 非模板流程必须在 `process_registry.json` 可发现，并标注生命周期状态。
