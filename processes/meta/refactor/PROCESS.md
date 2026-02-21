# refactor - Human Guide

## Objective

执行 M3 重构流程：objective/scope -> spec -> test prep -> implement -> regression gate -> lifecycle sync。

## Assets

- Runtime skill entry: `SKILL.md`
- Structured manifest: `process.json`

## Phase Summary

1. `p1` refactor-objective-and-scope (`meta.arch.objective-writer`)
2. `p2` refactor-spec-authoring (`meta.arch.spec-writer`)
3. `p3` refactor-test-preparation (`meta.qa.test-designer`)
4. `p4` refactor-implementation (`system.ops.manual-task`)
5. `p5` refactor-gate-evaluation (`meta.qa.llm-judge`)
6. `p6` lifecycle-gate-sync (`meta.arch.template-validator`)

## Control Rules

- 默认顺序执行。
- `p5` 失败最多回环到 `p4` 两次。
- 证据链断裂时 Fail-Closed。
