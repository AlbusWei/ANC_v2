# development-process - Human Guide

## Objective

以最小成本跑通 ANC v2 第一条元流程闭环：Objective -> Spec -> Test -> Implement -> Verify。

## Assets

- Runtime skill entry: `SKILL.md`
- Structured manifest: `process.json`

## Phase Summary

1. `p1` write-spec (`spec-writer`)
2. `p2` design-tests (`test-designer`)
3. `p3` implement (`manual-task`)
4. `p4` verify (`llm-judge`)

## Control Rules

- 默认顺序执行。
- `p4` 失败时最多回环到 `p3` 两次。
- 任一阶段缺证据则 Fail-Closed。
