# Trigger Governance Dry-Run Evidence

> 版本: v0.1.0 | 范围: 文档级 dry-run 证据组织约定

## 1. 路径约定

证据目录固定为：

`/Users/albus/MyProjects/ANC_v2_worktrees/review-layers-modules/docs/design/modules/evidence/trigger-governance/`

命名规则：

1. 用例证据：`<CASE-ID>-dry-run.md`
2. 同轮补充：`<CASE-ID>-dry-run-r<round>.md`

示例：

1. `TG-SCH-002-dry-run.md`
2. `TG-EVT-003-dry-run.md`

## 2. 最小模板

```md
# <CASE-ID> Dry-Run Evidence

## Metadata
- Date:
- Reviewer:
- Branch:
- Mode: doc-level dry-run / runtime dry-run

## Input Snapshot
- Trigger definition:
- Key payload:
- Preconditions:

## Expected Behaviour
- ...

## Simulated/Observed Steps
1. ...
2. ...

## Evidence Refs
- trigger_ref:
- instance_ref:
- fail_closed_ref:
- backfill_ref:

## Verdict
- Result: PASS / FAIL / BLOCKED / N/A
- Notes:
```

## 3. 升级策略

1. 当前阶段允许文档级 dry-run。
2. trigger runtime 资产落地后，同目录追加运行级 dry-run 证据，并在 checklist 回填路径。
