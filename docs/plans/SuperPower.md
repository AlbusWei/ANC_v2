# SuperPower 研发主链入口基线

## 目标

本文件作为 OpenClaw 运行时链路中的 `superpower_ref` 默认入口，用于声明当前回合遵循 SuperPower 主导研发语义，并为质量门禁与生命周期治理提供统一上下文引用。

## 约束

1. 研发主链遵循 `Objective -> Spec -> Test -> Development`。
2. 关键阶段必须执行 Fail-Closed：输入证据缺失、契约不闭合或引用不可达时直接失败。
3. 生命周期结论上限保持在 `review`，不在本文件内推动 `active`。

## 协议锚点

1. SuperPower 协同协议：`docs/design/interfaces/superpower-collaboration-protocol.md`
2. 施工治理原子流程：`docs/design/processes/atomic/AP-035-superpower-round-sync.md`
3. 会话与证据应在运行目录落盘：`tmp/runtime_data/` 或 `runtime_data/`

## 使用说明

1. 作为 `superpower_ref` 输入字段传入 `quality-gate-preparation`、`quality-gate-evaluation` 及上游主流程。
2. 如需扩展本回合具体策略，请在本文件追加章节，不得删除协议锚点。
