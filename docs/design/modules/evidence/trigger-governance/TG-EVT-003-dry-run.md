# TG-EVT-003 Dry-Run Evidence

## Metadata

- Date: 2026-02-21
- Reviewer: Codex
- Branch: `codex/review-layers-modules`
- Mode: doc-level dry-run

## Input Snapshot

- Trigger definition:
  - `trigger_type=event`
  - `canonical_event=internal.lifecycle.transitioned`
  - `match_rule=entity_type=skill && review->active`
- Event payload:
  - 缺失字段 `transition_evidence_ref`
- Preconditions:
  - M2 按最小字段做校验
  - 缺证据默认 Fail-Closed

## Expected Behaviour

1. 命中规则后在字段校验阶段拒绝执行。
2. 不输出结论性摘要，不推进后续实例。
3. 生成 `fail_closed_record` 与 `backfill_request`。

## Simulated Steps

1. 构造一条 `skill review->active` 事件，故意省略 `transition_evidence_ref`。
2. 经 `trigger matcher -> bpm` 执行字段校验。
3. 断言系统进入 Fail-Closed 分支并生成补数请求。

## Evidence Refs

- event_ref: `dryrun://event/TG-EVT-003/missing-evidence`
- fail_closed_ref: `dryrun://guard/TG-EVT-003/reject-missing-transition-evidence`
- backfill_request_ref: `dryrun://request/TG-EVT-003/backfill-transition-evidence`

## Verdict

- Result: PASS
- Notes: 覆盖“证据缺失拒绝推进 + 触发补数动作”的核心门禁语义。
