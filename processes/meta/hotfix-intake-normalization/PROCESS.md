# hotfix-intake-normalization - Process Guide

## Purpose

实现 hotfix profile 的 AP-001/AP-002 语义隔离，避免与通用开发 intake 链路混叠。

## Execution Phases

1. hotfix-objective-intake
2. impact-and-rollback-normalization

## Fail-Closed Rules

1. `incident_context_ref` 缺失。
2. 无法推导影响范围或回滚方向。
3. 证据链不完整。

## Runner Policy

1. 本流程是编排包装层，默认不新增 runner。
2. 实际执行由 skill/下级流程承担。
