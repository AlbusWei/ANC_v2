# implementation-execution-core - Process Guide

## Purpose

抽象 AP-006 实现执行语义，避免各主流程重复定义实现阶段契约。

## Execution Phases

1. implementation-execution

## Fail-Closed Rules

1. `spec_ref` 或 `test_plan_ref` 缺失。
2. 实施结果无法回填 `implementation_ref`。

## Runner Policy

1. 本流程是编排包装层，默认不新增 runner。
2. 实施动作由 `system.ops.manual-task` 执行。
