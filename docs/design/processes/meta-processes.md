# 元流程清单与设计

> 版本: v0.9.0 | 分类: Meta Processes | 最后更新: 2026-02-24

## 已有元流程

### development-process

- process_id: development-process
- canonical_path: `processes/meta/development-process/`
- level: P4
- process_role: 下游业务流程可复用的最小开发内核（仅覆盖 Objective->Spec->Test->Implement->Gate）
- phases: objective-scope-baseline -> spec-authoring-contract -> quality-gate-preparation -> implementation-execution-core -> quality-gate-evaluation
- loop: p5 fail 回到 p4，max 2
- collaboration pilot: 真实 OpenClaw 分发 + phase 级会话 reset 隔离（W11）

### quality-gate-preparation

- process_id: quality-gate-preparation
- design_doc: `docs/design/processes/quality-gate-preparation-process.md`
- level: P4
- phases: design-tests -> compile-test-datapoints -> bind-test-profiles
- output: test_plan_ref + preparation_bundle_ref

### quality-gate-evaluation

- process_id: quality-gate-evaluation
- design_doc: `docs/design/processes/quality-gate-evaluation-process.md`
- level: P4
- phases: run-objective-evaluation -> run-subjective-evaluation(optional) -> run-regression-evaluation -> aggregate-gate-decision
- output: final_gate_verdict_ref

### full-development

- process_id: full-development
- canonical_path: `processes/meta/full-development/`
- design_doc: `docs/design/processes/full-development-process.md`
- level: P4
- phases: objective-intake-and-scope -> spec-authoring -> quality-gate-preparation -> implementation-execution -> quality-gate-evaluation -> lifecycle-gate-sync -> release-packaging -> evolution-feedback-planning
- collaboration pilot: 真实 OpenClaw 分发 + phase 级会话 reset 隔离（W8）

### hotfix

- process_id: hotfix
- canonical_path: `processes/meta/hotfix/`
- design_doc: `docs/design/processes/hotfix-process.md`
- level: P4
- phases: hotfix-intake -> scope-and-spec-fast-baseline -> fast-test-preparation -> hotfix-implementation -> hotfix-gate-evaluation -> lifecycle-gate-sync -> release-packaging
- collaboration pilot: 真实 OpenClaw 分发 + phase 级会话 reset 隔离（W10）

### refactor

- process_id: refactor
- canonical_path: `processes/meta/refactor/`
- design_doc: `docs/design/processes/refactor-process.md`
- level: P4
- phases: refactor-objective-and-scope -> refactor-spec-authoring -> refactor-test-preparation -> refactor-implementation -> refactor-gate-evaluation -> lifecycle-gate-sync
- collaboration pilot: 真实 OpenClaw 分发 + phase 级会话 reset 隔离（W10）

### construction-plane-governance

- process_id: construction-plane-governance
- canonical_path: `processes/meta/construction-plane-governance/`
- design_doc: `docs/design/processes/construction-plane-governance-process.md`
- level: P4
- phases: scope-intake-and-baseline -> run-construction-audit -> execute-linked-updates -> sync-openspec-state -> verify-and-close

## 现行 P5 子流程库（M3 Phase2）

| P5 子流程 ID | 语义边界 | 主要调用方 |
|---|---|---|
| `objective-scope-baseline` | Objective + Scope baseline | `full-development.p1`, `refactor.p1`, `development-process.p1` |
| `hotfix-intake-normalization` | hotfix intake profile | `hotfix.p1` |
| `hotfix-scope-spec-baseline` | hotfix scope + spec baseline | `hotfix.p2` |
| `spec-authoring-contract` | 规格产出契约 | `full-development.p2`, `refactor.p2`, `development-process.p2` |
| `implementation-execution-core` | 实施执行核心 | `full-development.p4`, `hotfix.p4`, `refactor.p4`, `development-process.p4` |
| `release-packaging-governed` | 治理化发布打包 | `full-development.p7`, `hotfix.p7` |
| `evolution-feedback-planning` | 演化反馈规划 | `full-development.p8` |

## AP 入口语义（M3 Phase10）

1. 元流程 phase 统一使用 `target_type=subprocess`。
2. 当 phase 需要直接承载 AP 语义且暂无显式注册流程时，使用 `inline_ap`（临时 AP）承载 skill 映射。
3. 当 `inline_ap.actor == phase.actor` 且 `inline_ap.pierce_allowed=true` 时，允许运行时穿透执行（不新增递归栈帧）。
4. 长期目标为“临时 AP -> 显式注册 AP/P5 子流程”收敛，不在目标态长期保留 `inline_ap`。

## 递归组合规则

1. 元流程可组合 P5/P6 子流程。
2. 同层级组合允许，但必须声明终止条件。
3. 组合关系必须落盘到 `composed_processes[]`。
4. 存在生命周期断点的 phase 必须拆为多个复合流程并由父流程编排。

## 设计门禁（Fail-Closed）

1. 若出现一对多/多对多责任重叠且未给出解释与解耦策略，评审判定失败。
2. 若目标架构仍存在历史包装节点回流，评审判定失败。
