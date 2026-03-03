# Plans Workspace（回合工作台）

本目录是“当次协作回合”的工作文档区，不承载长期架构/设计权威。

长期权威文档位于：

1. `docs/architecture/`（架构与机制）
2. `docs/design/`（详细设计与契约）

`docs/plans/` 仅用于记录当前回合分析、方案推演与实施切分；回合结束后必须归档到 `docs/plans/archive/`。

## 使用规则

1. 新需求可先落在 `docs/plans/SSOT-design.md` / `docs/plans/SSOT-implementation.md` 作为工作草案。
2. 确认有效的长期结论后，必须同步写入 `docs/architecture/` 与 `docs/design/`。
3. 历史内容不留在工作台文件中，统一归档到 `docs/plans/archive/`。
4. `docs/plans` 不作为发布或运行时治理的长期 SSOT 入口。

## 变更记录

1. 2026-03-03：`docs/plans` 定位调整为“回合工作台 + 归档入口”，长期权威迁回 `docs/architecture` 与 `docs/design`。
