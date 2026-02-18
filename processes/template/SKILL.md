---
name: "process-template"
description: "ANC v2 process template. Use this asset as the baseline when creating a new BPM process package."
license: "Apache-2.0"
compatibility: "openclaw>=0.0.0; agentskills>=0.2"
metadata: {"category":"template","owner":"bpm","stability":"stable"}
allowed-tools: "Read Write Bash"
version: "0.1.0"
---

# process-template

用于初始化 Process 资产（`SKILL.md` + `process.json` + 可选 `PROCESS.md`）。

## Objective

定义可被 OpenClaw 识别且可被 BPM 执行的最小流程包。

## Invocation

- Entry manifest: `process.json`
- Initiator roles: bpm / architect
- Priority support: P0 / P1 / P2

## Input Contract

- Format: json
- Required fields:
  - objective_ref
  - input_payload

## Output Contract

- Format: json
- Required fields:
  - final_output
  - evidence_refs
  - verdict

## Runtime Rules

1. 每个 phase 必须声明 SIPOC。
2. I/O 校验失败时 Fail-Closed。
3. 所有 phase 输出必须可追溯到证据路径。

## References

- Manifest spec: `process.json`
- Human guide: `PROCESS.md`
