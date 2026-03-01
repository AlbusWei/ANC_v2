---
name: "evolution-feedback-planning"
description: "P5 子流程：AP-013/AP-014/AP-015/AP-017 演化反馈规划"
license: "Apache-2.0"
compatibility:
  openclaw: ">=2026.2"
  agentskills: ">=0.2"
allowed-tools:
  - Read
  - Write
  - Bash
version: "0.1.0"
---

# evolution-feedback-planning

## Objective

把发布后反馈到改进计划的链路固化为可复用子流程，确保演化证据和复盘产出闭合。

## Input Contract

- Format: json
- Required fields: feedback_evidence_ref

## Output Contract

- Format: json
- Required fields: improvement_plan_ref, retro_report_ref
