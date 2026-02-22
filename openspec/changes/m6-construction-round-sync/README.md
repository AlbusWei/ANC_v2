# m6-construction-round-sync

M6 runtime dry-run baseline for construction-plane-governance

## Why

M6 需要一个可重复执行的运行级回合样板，以验证 AP-032~AP-036 的契约闭合和 Fail-Closed 机制。

## What Changes

- 增加 M6 回合执行器与证据写入工具。
- 增加 M6 专项门禁 `verify-m6`。
- 新增 A/B/C 三种运行级 dry-run 证据。

## Impact

- 施工回合可在 CLI 下执行并输出结构化证据包。
- 回合对账与 OpenSpec 同步冲突可被脚本阻断。
