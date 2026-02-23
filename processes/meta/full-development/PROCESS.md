# full-development - Human Guide

## Objective

跑通 M3 全链路开发流程：Objective -> Spec -> Test Prep -> Implement -> Gate Eval -> Lifecycle -> Release -> Evolution Feedback。

## Assets

- Runtime skill entry: `SKILL.md`
- Structured manifest: `process.json`
- Runtime runner: `scripts/full_development_runner.py`

## Phase Summary

1. `p1` objective-intake-and-scope（`subprocess: objective-scope-baseline`，actor=`architect`）
2. `p2` spec-authoring（`subprocess: spec-authoring-contract`，actor=`architect`）
3. `p3` quality-gate-preparation（`subprocess: quality-gate-preparation`，actor=`qa`）
4. `p4` implementation-execution（`subprocess: implementation-execution-core`，actor=`kernel-dev`）
5. `p5` quality-gate-evaluation（`subprocess: quality-gate-evaluation`，actor=`qa`）
6. `p6` lifecycle-gate-sync（`subprocess: lifecycle-review`，actor=`admin`）
7. `p7` release-packaging（`subprocess: release-packaging-governed`，actor=`admin`）
8. `p8` evolution-feedback-planning（`subprocess: evolution-feedback-planning`，actor=`architect`）

## Control Rules

- 默认顺序执行。
- `p5` 失败最多回环到 `p4` 两次。
- 任一阶段缺证据则 Fail-Closed。

## Collaboration Pilot（P9）

1. 试点范围：`full-development`（按顺序推进，不做风险分层）。
2. 调度要求：真实 `openclaw` 分发，禁止仅本地模拟。
3. 会话策略：phase 级会话隔离；同 actor 相邻 phase 通过 `sessions.reset` 强制新会话。
4. 当前目标：先验证“可分发、可交接、可回放”，后续再逐步接入各子流程真实执行。
