---
name: "development-process"
description: "Phase 0.5 minimal development process for building a skill asset with tests and registry sync."
license: "Apache-2.0"
compatibility: "openclaw>=0.0.0; agentskills>=0.2"
metadata: {"category":"process","owner":"bpm","stability":"draft"}
allowed-tools: "Read Write Bash"
version: "0.1.0"
---

# development-process

最小化自开发流程：围绕一个 Skill 资产完成澄清、落盘、验证与注册。

## Objective

将 `Objective -> Spec -> Test -> Development` 链路固化为可执行流程资产。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: architect / bpm
- Priority support: P0 / P1 / P2

## Input Contract

- Format: json
- Required fields:
  - objective_ref
  - input_payload
  - target_skill_name

## Output Contract

- Format: json
- Required fields:
  - final_output
  - evidence_refs
  - verdict

## Runtime Rules

1. 每个 phase 产出必须可追溯到证据路径。
2. 测试资产未生成则不能进入 registry 同步阶段。
3. 任一阶段 I/O 校验失败时 Fail-Closed。

## References

- Manifest spec: `process.json`
- Human guide: `PROCESS.md`
