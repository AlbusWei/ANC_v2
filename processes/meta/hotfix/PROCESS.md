# hotfix - Human Guide

## Objective

执行 M3 紧急修复流程：快速 intake -> spec -> test prep -> implement -> gate -> lifecycle -> release。

## Assets

- Runtime skill entry: `SKILL.md`
- Structured manifest: `process.json`

## Phase Summary

1. `p1` hotfix-intake (`meta.arch.objective-writer`)
2. `p2` scope-and-spec-fast-baseline (`meta.arch.spec-writer`)
3. `p3` fast-test-preparation (`meta.qa.test-designer`)
4. `p4` hotfix-implementation (`system.ops.manual-task`)
5. `p5` hotfix-gate-evaluation (`meta.qa.llm-judge`)
6. `p6` lifecycle-gate-sync (`meta.arch.template-validator`)
7. `p7` release-packaging (`system.ops.manual-task`)

## Control Rules

- 默认顺序执行。
- `p5` 失败最多回环到 `p4` 一次。
- 无回滚计划或关键证据缺失时 Fail-Closed。
