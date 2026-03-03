# ANC v2 详细设计文档体系

> 版本: v0.2.0 | 状态: Active Draft | SSOT 上游: `docs/architecture/system_overview.md`

## 定位

本目录承接 `docs/architecture/` 的高层架构决策，向下展开为可实施的详细设计。

## 目录索引

| 目录 | 内容 |
|---|---|
| `layers/` | L0-L5 分层详细设计与最小定义矩阵 |
| `modules/` | M1-M6 模块设计与依赖矩阵 |
| `agents/` | kernel/control/app agent 设计与协作模式 |
| `skills/` | meta/system/business skill 设计与生命周期协议 |
| `processes/` | 递归流程架构、P1-P6 设计与原子流程目录 |
| `business/` | 双主线业务流程与复用映射 |
| `data-models/` | process/context/evidence/role 等 schema |
| `interfaces/` | BPM、registry、role handoff 等接口协议 + product lifecycle governance protocol |
| `inventories/` | agent/skill/process/component 全量清单 |
| `standards/` | Agent/Skill/Process/P1-P6 工程化标准 |

## 推荐阅读顺序

1. `docs/design/standards/README.md`
2. `docs/design/layers/layer-minimum-definition-matrix.md`
3. `docs/design/processes/recursive-process-architecture.md`
4. `docs/design/business/README.md`
5. `docs/design/processes/owner-evolution-governance-process.md`
6. `docs/design/interfaces/evolution-hook-event-protocol.md`
7. `docs/design/data-models/evolution-hook-event-schema.json`
8. inventories 与 interfaces/data-models

## 强制规则

1. 关键变更先更新 SSOT，再更新 design。
2. 任何资产变更必须回写 registry 与 inventory。
3. `development-process` canonical 路径固定为 `processes/meta/development-process/`。
4. 生命周期统一为 5 态：`draft -> review -> active -> deprecated -> retired`。
5. 若 `layers/` 或 `modules/` 发生职责/边界/依赖变化，必须在同回合补齐受影响的 `agents/`、`skills/`、`processes/` 设计文档，禁止“先注册后补文档”。
6. 新增 `agent/skill/process` 若缺对应设计文档，只能保持 `draft`，不得推进到 `review/active`。
