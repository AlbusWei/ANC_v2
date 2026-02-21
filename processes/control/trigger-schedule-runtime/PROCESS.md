# trigger-schedule-runtime - Human Guide

## Objective

把定时与心跳触发治理从文档提案推进为可执行流程资产。

## Assets

- Runtime skill entry: `SKILL.md`
- Structured manifest: `process.json`

## SIPOC Overview

| Element | Description |
|---|---|
| Supplier | schedule/heartbeat trigger source |
| Input | canonical trigger envelope |
| Process | normalize -> dedupe -> dispatch -> evidence -> catchup -> escalate |
| Output | trigger receipt + runtime trace |
| Client | downstream target process + governance audit |

## Roles

- Owner: bpm
- Actors: bpm
- Stakeholders: admin, owner
