# release-packaging-governed - Process Guide

## Purpose

将 AP-012 发布动作收敛为治理化 P5 子流程，固定发布决策与回滚契约输出。

## Execution Phases

1. release-packaging

## Fail-Closed Rules

1. 发布前置证据任一缺失。
2. `sys.admin.release-manager` 返回非可发布决策。
3. 回滚包或决策记录缺失。

## Runner Policy

1. 本流程是编排包装层，默认不新增 runner。
2. 发布动作由 `sys.admin.release-manager` 执行。
