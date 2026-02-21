# L3 — 自开发层详细设计

> 版本: v0.3.0 | 最后更新: 2026-02-21

## 层级定位

系统使用自身能力开发自身产品（Agent/Skill/Process）。

## 最小定义（七类）

- Agents: architect, qa, kernel-dev, admin, release-manager-agent
- Skills: objective-writer, spec-writer, test-designer, release-manager, impact-analyzer
- Processes: development-process, full-development, hotfix, refactor
- Components: dev artifacts, test artifacts, changelog
- Interfaces: task handoff, release interface
- Data Models: objective/spec/test/release schema
- Acceptance: Objective->Spec->Test->Dev->Verify->Release 全链可追溯

## 核心流程

1. development-process（canonical: `processes/meta/development-process/`）
2. full-development（canonical: `processes/meta/full-development/`）
3. hotfix（canonical: `processes/meta/hotfix/`）
4. refactor（canonical: `processes/meta/refactor/`）

## 约束

1. 不允许跳过测试。
2. 元层修改必须走 7 步门禁。
3. 发布必须经过 lifecycle-review。
