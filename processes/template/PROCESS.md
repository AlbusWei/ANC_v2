# process-template - Human Guide

## Objective

该模板用于初始化可执行、可审计的流程资产，并确保与 BPM/Agent Skills 双侧兼容。

## Assets

- Runtime skill entry: `SKILL.md`
- Structured manifest: `process.json`

## SIPOC Overview

| Element | Description |
|---|---|
| Supplier | Initiator / upstream process |
| Input | objective_ref + input_payload |
| Process | structured phase execution |
| Output | final_output + evidence_refs + verdict |
| Client | Initiator / downstream process |

## Roles

- Initiator: request owner
- Owner: bpm
- Actors: architect / kernel-dev / qa
- Stakeholders: objective owner

## Control Structures

默认使用 `sequence`，按需扩展 `condition`, `loop`, `fork_join`, `merge`。

## Copy Checklist

1. 复制 `template` 到 `processes/<process-name>`。
2. 修改 `SKILL.md` frontmatter `name`。
3. 修改 `process.json.process_id`。
4. 根据目标补全 phases 与验收条件。
