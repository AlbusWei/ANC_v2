# objective-scope-baseline - Process Guide

## Purpose

把 AP-001/AP-002/AP-003 的目标与范围语义拆分为连续、可追溯的 P5 编排子流程。

## Execution Phases

1. objective-intake
2. scope-normalization
3. scope-baseline-finalization

## Fail-Closed Rules

1. `objective_context_ref` 缺失或不可解析。
2. 目标与范围语义冲突且无法裁决。
3. 任一阶段无法产出可追溯证据。

## Runner Policy

1. 本流程是编排包装层，默认不新增 runner。
2. 执行动作下沉到 skill 或下级子流程，保持 DIP/LoD 约束。
