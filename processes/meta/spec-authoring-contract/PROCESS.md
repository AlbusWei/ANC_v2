# spec-authoring-contract - Process Guide

## Purpose

抽离 AP-004 为独立 P5 子流程，确保规格产出语义单一且可复用。

## Execution Phases

1. spec-authoring

## Fail-Closed Rules

1. `objective_ref` 或 `scope_baseline_ref` 缺失。
2. 输出 spec 无法解析或缺少关键契约段。

## Runner Policy

1. 本流程是编排包装层，默认不新增 runner。
2. 规格生成执行下沉到 `meta.arch.spec-writer`。
