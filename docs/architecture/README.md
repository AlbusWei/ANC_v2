# ANC v2 架构文档索引

最后更新：2026-02-18

## 文档定位

`docs/architecture/system_overview.md` 是架构唯一信源（SSOT）。
其余文档是执行细则、协议和协作视图，不得与 SSOT 冲突。

项目入口文件：`AGENTS.md`。

## 阅读顺序

1. `docs/architecture/system_overview.md`
2. `docs/architecture/process_architecture.md`
3. `docs/architecture/openclaw_interface.md`
4. `docs/architecture/registry_contracts.md`
5. `docs/architecture/test_methodology.md`
6. `docs/architecture/context_protocol.md`
7. `docs/architecture/construction_plane.md`
8. `docs/architecture/glossary.md`

## 变更规则

1. 架构级变更：先改 `system_overview.md`。
2. 流程机制变更：同步改 `process_architecture.md`。
3. OpenClaw 接口变更：同步改 `openclaw_interface.md`。
4. registry 字段或格式变更：同步改 `registry_contracts.md`。
5. 测试策略变更：同步改 `test_methodology.md`。
6. 上下文传递规则变更：同步改 `context_protocol.md`。
7. 阶段计划变化：同步改 `construction_plane.md`。

## 当前目标

ANC v2 当前目标是先完成可执行约束体系，再进入能力实现，避免"未塑形先自动化"。

## 详细设计文档

架构文档定义"是什么"和"为什么"，详细设计文档定义"具体包含什么"和"怎么交互"。

详细设计索引：`docs/design/README.md`

包含：六层详细设计、六模块详细设计、Agent/Skill/Process 详细设计、数据模型、接口协议、资产清单。
