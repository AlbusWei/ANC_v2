# full-development - Human Guide

## Objective

跑通 M3 全链路开发流程：Objective -> Spec -> Test Prep -> Implement -> Gate Eval -> Lifecycle -> Release -> Evolution Feedback。

## Assets

- Runtime skill entry: `SKILL.md`
- Structured manifest: `process.json`

## Phase Summary

1. `p1` objective-intake-and-scope (`meta.arch.objective-writer`)
2. `p2` spec-authoring (`meta.arch.spec-writer`)
3. `p3` quality-gate-preparation（`subprocess: quality-gate-preparation`）
4. `p4` implementation-execution (`system.ops.manual-task`)
5. `p5` quality-gate-evaluation（`subprocess: quality-gate-evaluation`）
6. `p6` lifecycle-gate-sync (`meta.arch.template-validator`)
7. `p7` release-packaging (`system.ops.manual-task`)
8. `p8` evolution-feedback-planning (`meta.arch.process-creator`)

## Control Rules

- 默认顺序执行。
- `p5` 失败最多回环到 `p4` 两次。
- 任一阶段缺证据则 Fail-Closed。
