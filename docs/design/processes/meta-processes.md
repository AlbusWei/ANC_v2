# 元流程清单与设计

> 版本: v0.5.0 | 分类: Meta Processes | 最后更新: 2026-02-21

## 已有元流程

### development-process

- process_id: development-process
- canonical_path: `processes/meta/development-process/`
- level: P4
- phases: write-spec -> design-tests -> implement -> verify
- loop: p4 fail 回到 p3，max 2

### quality-gate-preparation（新增设计）

- process_id: quality-gate-preparation
- design_doc: `/Users/albus/MyProjects/ANC_v2/docs/design/processes/quality-gate-preparation-process.md`
- level: P4
- phases: design-tests -> compile-test-datapoints -> bind-test-profiles
- output: preparation_bundle_ref

### quality-gate-evaluation（新增设计）

- process_id: quality-gate-evaluation
- design_doc: `/Users/albus/MyProjects/ANC_v2/docs/design/processes/quality-gate-evaluation-process.md`
- level: P4
- phases: run-objective-evaluation -> run-subjective-evaluation(optional) -> run-regression-evaluation -> aggregate-gate-decision
- output: gate_decision + evidence package

### full-development（本轮新增）

- process_id: full-development
- canonical_path: `processes/meta/full-development/`
- design_doc: `docs/design/processes/full-development-process.md`
- level: P4
- phases: objective-intake-and-scope -> spec-authoring -> quality-gate-preparation -> implementation-execution -> quality-gate-evaluation -> lifecycle-gate-sync -> release-packaging -> evolution-feedback-planning

### hotfix（本轮新增）

- process_id: hotfix
- canonical_path: `processes/meta/hotfix/`
- design_doc: `docs/design/processes/hotfix-process.md`
- level: P4
- phases: hotfix-intake -> scope-and-spec-fast-baseline -> fast-test-preparation -> hotfix-implementation -> hotfix-gate-evaluation -> lifecycle-gate-sync -> release-packaging

### refactor（本轮新增）

- process_id: refactor
- canonical_path: `processes/meta/refactor/`
- design_doc: `docs/design/processes/refactor-process.md`
- level: P4
- phases: refactor-objective-and-scope -> refactor-spec-authoring -> refactor-test-preparation -> refactor-implementation -> refactor-gate-evaluation -> lifecycle-gate-sync

## 递归组合规则

1. 元流程可组合 P5/P6 子流程。
2. 同层级组合允许，但必须声明终止条件。
3. 组合关系必须落盘到 `composed_processes[]`。
4. 存在生命周期断点的 phase 必须拆为多个复合流程并由父流程编排。
