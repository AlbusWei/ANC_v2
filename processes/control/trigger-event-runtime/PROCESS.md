# trigger-event-runtime - Human Guide

## Objective

把事件触发治理从文档提案推进为可执行流程资产，覆盖 TG-EVT 系列场景。

## Assets

- Runtime skill entry: `SKILL.md`
- Structured manifest: `process.json`

## SIPOC Overview

| Element | Description |
|---|---|
| Supplier | lifecycle or business event source |
| Input | canonical event envelope |
| Process | normalize -> dedupe -> dispatch -> evidence -> backfill/catchup -> escalate |
| Output | trigger receipt + dedupe decision + traceability |
| Client | downstream target process + governance audit |

## Roles

- Owner: bpm
- Actors: bpm
- Stakeholders: hr, admin
