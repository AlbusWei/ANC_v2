# development-process - Human Guide

## Objective

为 Phase 0.5 提供可执行的最简自开发流程，确保 Skill 资产从需求到 registry 同步有完整证据链。

> 状态说明：本目录为 Phase 0.5 示例归档，不作为运行时流程 SSOT。运行基线请使用 `/Users/albus/MyProjects/ANC_v2/processes/meta/development-process/`。

## Assets

- Runtime skill entry: `SKILL.md`
- Structured manifest: `process.json`

## SIPOC Overview

| Element | Description |
|---|---|
| Supplier | initiator |
| Input | objective_ref + input_payload + target_skill_name |
| Process | 4-phase development flow |
| Output | final_output + evidence_refs + verdict |
| Client | initiator |

## Roles

- Initiator: objective owner
- Owner: bpm
- Actors: architect / qa / bpm
- Stakeholders: objective owner, system architect

## Phase Notes

### Phase 1: clarify-objective-and-scope

- Actor: architect
- Skill/Process: `skill-creator`
- Acceptance Criteria: objective 和约束明确

### Phase 2: author-skill-asset

- Actor: architect
- Skill/Process: `skill-creator`
- Acceptance Criteria: 技能资产落盘且 frontmatter 可解析

### Phase 3: design-and-run-tests

- Actor: qa
- Skill/Process: `skill-creator`
- Acceptance Criteria: 测试资产与证据存在

### Phase 4: sync-registry

- Actor: bpm
- Skill/Process: `skill-creator`
- Acceptance Criteria: registry 与资产字段一致
