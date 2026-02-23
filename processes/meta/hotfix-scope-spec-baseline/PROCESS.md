# hotfix-scope-spec-baseline - Process Guide

## Purpose

在 hotfix 场景中先固化 AP-003 范围基线，再复用 `spec-authoring-contract` 产出规格，避免 AP-004 重复内联。

## Execution Phases

1. hotfix-scope-baseline
2. hotfix-spec-authoring

## Fail-Closed Rules

1. `hotfix_objective_ref` 或 `impact_scope_ref` 缺失。
2. 子流程 `spec-authoring-contract` 返回失败。
3. 结果映射 `spec_ref -> hotfix_spec_ref` 未完成。

## Runner Policy

1. 本流程是编排包装层，默认不新增 runner。
2. AP-004 执行由子流程 `spec-authoring-contract` 承担。
