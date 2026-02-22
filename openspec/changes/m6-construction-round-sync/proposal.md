## Why

M6 需要一个可重复执行的运行级回合样板，以验证 AP-032~AP-036 的契约闭合和 Fail-Closed 机制。当前只有文档定义，缺少可执行闭环与专项门禁。

## What Changes

- 新增 M6 回合执行脚本（AP-032/033/034/036 执行器 + round evidence 工具 + run_round 编排器）。
- 改造 OpenSpec 同步执行脚本，使其按完整 schema 产出并在冲突/对账异常时阻断。
- 增加 `verify-m6` 专项门禁，对回合证据、AP 覆盖、预关闭门禁做校验。
- 补充运行契约基线文档与样例 payload。

## Capabilities

### New Capabilities
- `construction-plane-runtime-round`: 执行并验证 M6 施工治理回合，输出结构化证据包与阻断原因。

### Modified Capabilities
- `construction-plane`: 从文档级治理升级为可执行运行级治理，增加 round evidence 对账门禁。

## Impact

- 影响 `processes/meta/construction-plane-governance/` 运行脚本与 manifest 契约描述。
- 影响 `skills/system/manual-task`、`skills/system/construction-audit`、`skills/system/openspec-sync` 的运行实现。
- 影响 `shared/registry/registry_contract_tool.py` 命令接口（新增 `verify-m6`）。
