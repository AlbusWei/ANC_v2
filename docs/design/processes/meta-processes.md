# 元流程清单与设计

> 版本: v0.5.0 | 分类: Meta Processes

## 已有元流程（已注册）

### development-process

- process_id: development-process
- canonical_path: `processes/meta/development-process/`
- level: P4
- phases: write-spec -> design-tests -> implement -> verify
- loop: p4 fail 回到 p3，max 2

### quality-gate-preparation

- process_id: quality-gate-preparation
- canonical_path: `processes/meta/quality-gate-preparation/`
- level: P4
- phases: design-tests -> compile-test-datapoints -> bind-test-profiles
- output: preparation_bundle_ref

### quality-gate-evaluation

- process_id: quality-gate-evaluation
- canonical_path: `processes/meta/quality-gate-evaluation/`
- level: P4
- phases: run-objective-evaluation -> run-subjective-evaluation -> run-regression-evaluation -> aggregate-gate-decision -> govern-hold(on hold)
- output: gate_decision + evidence package

### hold-governance

- process_id: hold-governance
- canonical_path: `processes/meta/hold-governance/`
- level: P4
- phases: collect-progress-evidence -> triage-and-classify -> execute-triage-action -> health-maintenance -> close-or-escalate
- output: triage_report_ref + hold_resolution_ref

## 规划元流程

1. full-development
2. hotfix
3. refactor

## 递归组合规则

1. 元流程可组合 P5/P6 子流程。
2. 同层级组合允许，但必须声明终止条件。
3. 组合关系必须落盘到 `composed_processes[]`。
4. 存在生命周期断点的 phase 必须拆为多个复合流程并由父流程编排。
